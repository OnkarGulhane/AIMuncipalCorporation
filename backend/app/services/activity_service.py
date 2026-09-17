from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.case import Case, CaseTimeline, CaseStatus
from app.models.activity import (
    CaseMessage,
    InternalNote,
    CaseTask,
    CaseInvestigation,
    TaskStatus,
)
from app.schemas.activity import (
    CaseMessageCreate,
    CaseMessageResponse,
    InternalNoteCreate,
    InternalNoteResponse,
    CaseTaskCreate,
    CaseTaskUpdate,
    CaseTaskResponse,
    CaseInvestigationCreate,
    CaseInvestigationResponse,
)


class ActivityService:
    @staticmethod
    def _get_case_with_access(db: Session, case_id: int, user: User) -> Case:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found.",
            )
        if user.role == UserRole.REQUESTER and case.citizen_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access activities for this case.",
            )
        return case

    @staticmethod
    def _require_staff(user: User):
        if user.role == UserRole.REQUESTER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requesters are not permitted to perform internal staff operations.",
            )

    # -----------------------------------------------------------------------
    # Case Messages (Citizen <-> Staff)
    # -----------------------------------------------------------------------
    @staticmethod
    def list_messages(db: Session, case_id: int, user: User) -> List[CaseMessageResponse]:
        ActivityService._get_case_with_access(db, case_id, user)
        messages = (
            db.query(CaseMessage)
            .filter(CaseMessage.case_id == case_id)
            .order_by(CaseMessage.created_at.asc())
            .all()
        )
        results = []
        for msg in messages:
            results.append(
                CaseMessageResponse(
                    id=msg.id,
                    case_id=msg.case_id,
                    sender_id=msg.sender_id,
                    sender_name=msg.sender.full_name if msg.sender else None,
                    sender_role=msg.sender.role if msg.sender else None,
                    message=msg.message,
                    message_type=msg.message_type,
                    is_from_citizen=msg.is_from_citizen,
                    created_at=msg.created_at,
                )
            )
        return results

    @staticmethod
    def create_message(
        db: Session, case_id: int, data: CaseMessageCreate, user: User
    ) -> CaseMessageResponse:
        case = ActivityService._get_case_with_access(db, case_id, user)
        is_from_citizen = (user.role == UserRole.REQUESTER)

        msg = CaseMessage(
            case_id=case_id,
            sender_id=user.id,
            message=data.message,
            message_type=data.message_type.value if hasattr(data.message_type, "value") else str(data.message_type),
            is_from_citizen=is_from_citizen,
        )
        db.add(msg)

        # Timeline event
        action_name = "citizen_message" if is_from_citizen else "staff_message"
        timeline_entry = CaseTimeline(
            case_id=case_id,
            actor_id=user.id,
            action=action_name,
            notes=f"Message: {data.message[:80]}..." if len(data.message) > 80 else f"Message: {data.message}",
            is_internal=False,
        )
        db.add(timeline_entry)

        db.commit()
        db.refresh(msg)

        from app.services.notification_service import notification_service
        from app.models.notification import NotificationEventType

        if is_from_citizen:
            notification_service.dispatch_case_event_notifications(
                db=db,
                case=case,
                event_type=NotificationEventType.CITIZEN_RESPONSE.value,
                title=f"Citizen Message on #{case.case_number}",
                message=f"{user.full_name or 'Citizen'}: {data.message[:120]}",
                exclude_user_id=user.id,
            )
        else:
            event_type = (
                NotificationEventType.INFORMATION_REQUESTED.value
                if getattr(data, "message_type", None) == "request_info"
                else NotificationEventType.STAFF_UPDATE.value
            )
            notification_service.dispatch_case_event_notifications(
                db=db,
                case=case,
                event_type=event_type,
                title=f"Staff Update on #{case.case_number}",
                message=f"Municipal update: {data.message[:120]}",
                exclude_user_id=user.id,
            )

        return CaseMessageResponse(
            id=msg.id,
            case_id=msg.case_id,
            sender_id=msg.sender_id,
            sender_name=user.full_name,
            sender_role=user.role,
            message=msg.message,
            message_type=msg.message_type,
            is_from_citizen=msg.is_from_citizen,
            created_at=msg.created_at,
        )

    # -----------------------------------------------------------------------
    # Internal Notes (Staff-only)
    # -----------------------------------------------------------------------
    @staticmethod
    def list_internal_notes(db: Session, case_id: int, user: User) -> List[InternalNoteResponse]:
        ActivityService._require_staff(user)
        ActivityService._get_case_with_access(db, case_id, user)

        notes = (
            db.query(InternalNote)
            .filter(InternalNote.case_id == case_id)
            .order_by(InternalNote.created_at.desc())
            .all()
        )
        results = []
        for n in notes:
            results.append(
                InternalNoteResponse(
                    id=n.id,
                    case_id=n.case_id,
                    author_id=n.author_id,
                    author_name=n.author.full_name if n.author else None,
                    author_role=n.author.role if n.author else None,
                    note=n.note,
                    note_type=n.note_type,
                    created_at=n.created_at,
                )
            )
        return results

    @staticmethod
    def create_internal_note(
        db: Session, case_id: int, data: InternalNoteCreate, user: User
    ) -> InternalNoteResponse:
        ActivityService._require_staff(user)
        ActivityService._get_case_with_access(db, case_id, user)

        note_type_str = data.note_type.value if hasattr(data.note_type, "value") else str(data.note_type)
        note = InternalNote(
            case_id=case_id,
            author_id=user.id,
            note=data.note,
            note_type=note_type_str,
        )
        db.add(note)

        # Timeline event marked internal so citizens never see it
        timeline_entry = CaseTimeline(
            case_id=case_id,
            actor_id=user.id,
            action="internal_note_added",
            notes=f"Private note added ({note_type_str})",
            is_internal=True,
        )
        db.add(timeline_entry)

        db.commit()
        db.refresh(note)

        return InternalNoteResponse(
            id=note.id,
            case_id=note.case_id,
            author_id=note.author_id,
            author_name=user.full_name,
            author_role=user.role,
            note=note.note,
            note_type=note.note_type,
            created_at=note.created_at,
        )

    # -----------------------------------------------------------------------
    # Case Tasks
    # -----------------------------------------------------------------------
    @staticmethod
    def list_tasks(db: Session, case_id: int, user: User) -> List[CaseTaskResponse]:
        ActivityService._get_case_with_access(db, case_id, user)
        tasks = (
            db.query(CaseTask)
            .filter(CaseTask.case_id == case_id)
            .order_by(CaseTask.order.asc(), CaseTask.created_at.asc())
            .all()
        )
        results = []
        for t in tasks:
            results.append(
                CaseTaskResponse(
                    id=t.id,
                    case_id=t.case_id,
                    title=t.title,
                    description=t.description,
                    status=t.status,
                    assigned_to_id=t.assigned_to_id,
                    assigned_to_name=t.assigned_to.full_name if t.assigned_to else None,
                    created_by_id=t.created_by_id,
                    created_by_name=t.created_by.full_name if t.created_by else None,
                    due_date=t.due_date,
                    completed_at=t.completed_at,
                    order=t.order,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
            )
        return results

    @staticmethod
    def create_task(
        db: Session, case_id: int, data: CaseTaskCreate, user: User
    ) -> CaseTaskResponse:
        ActivityService._require_staff(user)
        case = ActivityService._get_case_with_access(db, case_id, user)

        task = CaseTask(
            case_id=case_id,
            title=data.title,
            description=data.description,
            status=TaskStatus.PENDING.value,
            assigned_to_id=data.assigned_to_id,
            created_by_id=user.id,
            due_date=data.due_date,
            order=data.order or 0,
        )
        db.add(task)

        # Timeline event
        timeline_entry = CaseTimeline(
            case_id=case_id,
            actor_id=user.id,
            action="task_created",
            notes=f"Task added: {data.title}",
            is_internal=False,
        )
        db.add(timeline_entry)

        db.commit()
        db.refresh(task)

        if task.assigned_to_id and task.assigned_to_id != user.id:
            from app.services.notification_service import notification_service
            from app.models.notification import NotificationEventType

            notification_service.create_notification(
                db=db,
                user_id=task.assigned_to_id,
                title=f"Task Assigned: #{case.case_number}",
                message=f"You have been assigned task '{task.title}' for case #{case.case_number}",
                event_type=NotificationEventType.TASK_ASSIGNED.value,
                case_id=case.id,
            )

        return CaseTaskResponse(
            id=task.id,
            case_id=task.case_id,
            title=task.title,
            description=task.description,
            status=task.status,
            assigned_to_id=task.assigned_to_id,
            assigned_to_name=task.assigned_to.full_name if task.assigned_to else None,
            created_by_id=task.created_by_id,
            created_by_name=user.full_name,
            due_date=task.due_date,
            completed_at=task.completed_at,
            order=task.order,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    @staticmethod
    def update_task(
        db: Session, case_id: int, task_id: int, data: CaseTaskUpdate, user: User
    ) -> CaseTaskResponse:
        ActivityService._require_staff(user)
        ActivityService._get_case_with_access(db, case_id, user)

        task = (
            db.query(CaseTask)
            .filter(CaseTask.id == task_id, CaseTask.case_id == case_id)
            .first()
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found on this case.",
            )

        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.assigned_to_id is not None:
            task.assigned_to_id = data.assigned_to_id
        if data.due_date is not None:
            task.due_date = data.due_date
        if data.order is not None:
            task.order = data.order

        if data.status is not None:
            new_status_str = data.status.value if hasattr(data.status, "value") else str(data.status)
            if new_status_str == TaskStatus.COMPLETED.value and task.status != TaskStatus.COMPLETED.value:
                task.completed_at = datetime.now(timezone.utc)
            elif new_status_str != TaskStatus.COMPLETED.value:
                task.completed_at = None
            task.status = new_status_str

            # Timeline event
            timeline_entry = CaseTimeline(
                case_id=case_id,
                actor_id=user.id,
                action="task_updated",
                notes=f"Task '{task.title}' status updated to {new_status_str}",
                is_internal=False,
            )
            db.add(timeline_entry)

        db.commit()
        db.refresh(task)

        return CaseTaskResponse(
            id=task.id,
            case_id=task.case_id,
            title=task.title,
            description=task.description,
            status=task.status,
            assigned_to_id=task.assigned_to_id,
            assigned_to_name=task.assigned_to.full_name if task.assigned_to else None,
            created_by_id=task.created_by_id,
            created_by_name=task.created_by.full_name if task.created_by else None,
            due_date=task.due_date,
            completed_at=task.completed_at,
            order=task.order,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    # -----------------------------------------------------------------------
    # Case Investigations
    # -----------------------------------------------------------------------
    @staticmethod
    def list_investigations(
        db: Session, case_id: int, user: User
    ) -> List[CaseInvestigationResponse]:
        ActivityService._require_staff(user)
        ActivityService._get_case_with_access(db, case_id, user)

        investigations = (
            db.query(CaseInvestigation)
            .filter(CaseInvestigation.case_id == case_id)
            .order_by(CaseInvestigation.created_at.desc())
            .all()
        )
        results = []
        for inv in investigations:
            results.append(
                CaseInvestigationResponse(
                    id=inv.id,
                    case_id=inv.case_id,
                    investigator_id=inv.investigator_id,
                    investigator_name=inv.investigator.full_name if inv.investigator else None,
                    observations=inv.observations,
                    actions_taken=inv.actions_taken,
                    findings=inv.findings,
                    evidence_notes=inv.evidence_notes,
                    follow_up_requirements=inv.follow_up_requirements,
                    created_at=inv.created_at,
                    updated_at=inv.updated_at,
                )
            )
        return results

    @staticmethod
    def create_investigation(
        db: Session, case_id: int, data: CaseInvestigationCreate, user: User
    ) -> CaseInvestigationResponse:
        ActivityService._require_staff(user)
        case = ActivityService._get_case_with_access(db, case_id, user)

        inv = CaseInvestigation(
            case_id=case_id,
            investigator_id=user.id,
            observations=data.observations,
            actions_taken=data.actions_taken,
            findings=data.findings,
            evidence_notes=data.evidence_notes,
            follow_up_requirements=data.follow_up_requirements,
        )
        db.add(inv)

        # Progress lifecycle state if in early stage
        target_status = None
        if data.actions_taken and data.actions_taken.strip():
            target_status = CaseStatus.ACTION_TAKEN.value
        elif case.status in [CaseStatus.REPORTED.value, CaseStatus.UNDERSTOOD.value, CaseStatus.ASSIGNED.value]:
            target_status = CaseStatus.INVESTIGATED.value

        if target_status and target_status != case.status:
            old_status = case.status
            case.status = target_status
            db.add(
                CaseTimeline(
                    case_id=case_id,
                    actor_id=user.id,
                    action="status_change",
                    old_value=old_status,
                    new_value=target_status,
                    notes=f"Auto-transitioned on investigation recording.",
                    is_internal=False,
                )
            )

        # Timeline event for investigation
        timeline_entry = CaseTimeline(
            case_id=case_id,
            actor_id=user.id,
            action="investigation_recorded",
            notes=f"Investigation findings logged: {data.findings[:80] if data.findings else 'Observations & actions recorded'}",
            is_internal=False,
        )
        db.add(timeline_entry)

        db.commit()
        db.refresh(inv)

        return CaseInvestigationResponse(
            id=inv.id,
            case_id=inv.case_id,
            investigator_id=inv.investigator_id,
            investigator_name=user.full_name,
            observations=inv.observations,
            actions_taken=inv.actions_taken,
            findings=inv.findings,
            evidence_notes=inv.evidence_notes,
            follow_up_requirements=inv.follow_up_requirements,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
        )


activity_service = ActivityService()
