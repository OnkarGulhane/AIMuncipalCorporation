from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.case import Case, CaseStatus, CaseTimeline
from app.models.user import User, UserRole
from app.models.escalation import CaseEscalation, EscalationStatus, EscalationTrigger
from app.schemas.escalation import EscalationCreate, EscalationUpdate, EscalationResponse


def create_case_escalation(
    db: Session,
    case: Case,
    escalation_data: EscalationCreate,
    current_user: Optional[User] = None,
) -> CaseEscalation:
    """
    Creates a new escalation for a case and logs a timeline event.
    """
    # Check if there is already an active escalation with the same trigger to prevent spam
    existing_active = (
        db.query(CaseEscalation)
        .filter(
            CaseEscalation.case_id == case.id,
            CaseEscalation.status == EscalationStatus.ACTIVE.value,
            CaseEscalation.trigger_type == escalation_data.trigger_type,
        )
        .first()
    )
    if existing_active:
        return existing_active

    escalation = CaseEscalation(
        case_id=case.id,
        escalated_by_id=current_user.id if current_user else None,
        escalated_to_id=escalation_data.escalated_to_id,
        trigger_type=escalation_data.trigger_type,
        reason=escalation_data.reason,
        status=EscalationStatus.ACTIVE.value,
    )
    db.add(escalation)

    # Flag case as escalated
    case.is_escalated = True
    if case.status not in {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value, CaseStatus.CANCELLED.value}:
        case.status = CaseStatus.ESCALATED.value

    # Log timeline event
    escalator_name = current_user.full_name if current_user else "Automated SLA/Risk System"
    timeline_entry = CaseTimeline(
        case_id=case.id,
        actor_id=current_user.id if current_user else None,
        action="case_escalated",
        new_value=f"Trigger: {escalation_data.trigger_type}",
        notes=f"Escalated by {escalator_name}: {escalation_data.reason}",
        is_internal=True,
    )
    db.add(timeline_entry)

    db.commit()
    db.refresh(escalation)

    from app.services.notification_service import notification_service
    from app.models.notification import NotificationEventType

    notification_service.dispatch_case_event_notifications(
        db=db,
        case=case,
        event_type=NotificationEventType.ESCALATION.value,
        title=f"Case Escalated: #{case.case_number}",
        message=f"Case '{case.title}' escalated ({escalation.trigger_type}): {escalation.reason}",
        exclude_user_id=current_user.id if current_user else None,
    )

    return escalation


def update_case_escalation(
    db: Session,
    escalation: CaseEscalation,
    update_data: EscalationUpdate,
    current_user: User,
) -> CaseEscalation:
    """
    Updates the status and resolution notes of an escalation.
    """
    old_status = escalation.status
    escalation.status = update_data.status
    if update_data.resolution_notes:
        escalation.resolution_notes = update_data.resolution_notes

    if update_data.status in {EscalationStatus.RESOLVED.value, EscalationStatus.DISMISSED.value}:
        escalation.resolved_by_id = current_user.id
        escalation.resolved_at = datetime.now(timezone.utc)

    # Check if there are any other remaining active escalations for this case
    remaining_active = (
        db.query(CaseEscalation)
        .filter(
            CaseEscalation.case_id == escalation.case_id,
            CaseEscalation.id != escalation.id,
            CaseEscalation.status == EscalationStatus.ACTIVE.value,
        )
        .count()
    )

    case = db.query(Case).filter(Case.id == escalation.case_id).first()
    if case and remaining_active == 0 and update_data.status in {EscalationStatus.RESOLVED.value, EscalationStatus.DISMISSED.value}:
        case.is_escalated = False
        if case.status == CaseStatus.ESCALATED.value:
            case.status = CaseStatus.ASSIGNED.value if case.assigned_to_id else CaseStatus.UNDERSTOOD.value

    # Log timeline event
    timeline_entry = CaseTimeline(
        case_id=escalation.case_id,
        actor_id=current_user.id,
        action="escalation_resolved" if update_data.status == EscalationStatus.RESOLVED.value else "escalation_updated",
        old_value=old_status,
        new_value=update_data.status,
        notes=update_data.resolution_notes or f"Escalation marked as {update_data.status}",
        is_internal=True,
    )
    db.add(timeline_entry)

    db.commit()
    db.refresh(escalation)

    if case:
        from app.services.notification_service import notification_service
        from app.models.notification import NotificationEventType

        ev_type = (
            NotificationEventType.ESCALATION_RESOLVED.value
            if update_data.status == EscalationStatus.RESOLVED.value
            else NotificationEventType.STATUS_CHANGED.value
        )
        notification_service.dispatch_case_event_notifications(
            db=db,
            case=case,
            event_type=ev_type,
            title=f"Escalation Updated: #{case.case_number}",
            message=f"Escalation on case '{case.title}' status changed to {update_data.status}.",
            exclude_user_id=current_user.id,
        )

    return escalation


def build_escalation_response(escalation: CaseEscalation) -> EscalationResponse:
    return EscalationResponse(
        id=escalation.id,
        case_id=escalation.case_id,
        case_number=escalation.case_rel.case_number if escalation.case_rel else None,
        case_title=escalation.case_rel.title if escalation.case_rel else None,
        escalated_by_id=escalation.escalated_by_id,
        escalated_by_name=escalation.escalated_by.full_name if escalation.escalated_by else "Automated System",
        escalated_to_id=escalation.escalated_to_id,
        escalated_to_name=escalation.escalated_to.full_name if escalation.escalated_to else None,
        trigger_type=escalation.trigger_type,
        reason=escalation.reason,
        status=escalation.status,
        resolution_notes=escalation.resolution_notes,
        resolved_by_id=escalation.resolved_by_id,
        resolved_by_name=escalation.resolved_by.full_name if escalation.resolved_by else None,
        resolved_at=escalation.resolved_at,
        created_at=escalation.created_at,
    )
