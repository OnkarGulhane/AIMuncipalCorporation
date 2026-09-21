import datetime
from typing import List, Optional, Tuple, Any
from sqlalchemy import or_, and_, func, desc, asc
from sqlalchemy.orm import Session
from app.models.case import Case, CaseTimeline, CaseStatus, CasePriority, CaseSeverity
from app.models.organization import Category
from app.models.user import User, UserRole
from app.models.activity import CaseMessage, InternalNote, CaseTask, CaseInvestigation
from app.models.attachment import CaseAttachment
from app.models.ai_analysis import AIAnalysis
from app.models.escalation import CaseEscalation
from app.models.sla import CaseSLA, SLAStatus
from app.schemas.case import CaseCreate, CaseUpdate, CaseStatusUpdate, CaseAssignmentUpdate, UnifiedTimelineItem, UnifiedTimelineResponse
from app.services.audit_service import audit_service


# Valid State Transitions Graph
VALID_TRANSITIONS = {
    CaseStatus.REPORTED.value: [
        CaseStatus.UNDERSTOOD.value,
        CaseStatus.ASSIGNED.value,
        CaseStatus.WAITING_INFO.value,
        CaseStatus.DUPLICATE.value,
        CaseStatus.CANCELLED.value,
    ],
    CaseStatus.UNDERSTOOD.value: [
        CaseStatus.ASSIGNED.value,
        CaseStatus.WAITING_INFO.value,
        CaseStatus.DUPLICATE.value,
        CaseStatus.CANCELLED.value,
    ],
    CaseStatus.ASSIGNED.value: [
        CaseStatus.INVESTIGATED.value,
        CaseStatus.ACTION_TAKEN.value,
        CaseStatus.WAITING_INFO.value,
        CaseStatus.ESCALATED.value,
        CaseStatus.CANCELLED.value,
    ],
    CaseStatus.INVESTIGATED.value: [
        CaseStatus.ACTION_TAKEN.value,
        CaseStatus.RESOLUTION_PROPOSED.value,
        CaseStatus.WAITING_INFO.value,
        CaseStatus.ESCALATED.value,
        CaseStatus.CANCELLED.value,
    ],
    CaseStatus.ACTION_TAKEN.value: [
        CaseStatus.RESOLUTION_PROPOSED.value,
        CaseStatus.INVESTIGATED.value,
        CaseStatus.WAITING_INFO.value,
        CaseStatus.ESCALATED.value,
        CaseStatus.CANCELLED.value,
    ],
    CaseStatus.RESOLUTION_PROPOSED.value: [
        CaseStatus.CONFIRMED.value,
        CaseStatus.REOPENED.value,
        CaseStatus.CLOSED.value,
        CaseStatus.ACTION_TAKEN.value,
    ],
    CaseStatus.CONFIRMED.value: [
        CaseStatus.CLOSED.value,
        CaseStatus.REOPENED.value,
    ],
    CaseStatus.CLOSED.value: [
        CaseStatus.REOPENED.value,
    ],
    CaseStatus.REOPENED.value: [
        CaseStatus.ASSIGNED.value,
        CaseStatus.INVESTIGATED.value,
        CaseStatus.ACTION_TAKEN.value,
        CaseStatus.ESCALATED.value,
        CaseStatus.CANCELLED.value,
    ],
    CaseStatus.WAITING_INFO.value: [
        CaseStatus.REPORTED.value,
        CaseStatus.UNDERSTOOD.value,
        CaseStatus.ASSIGNED.value,
        CaseStatus.INVESTIGATED.value,
        CaseStatus.ACTION_TAKEN.value,
        CaseStatus.CANCELLED.value,
    ],
    CaseStatus.ESCALATED.value: [
        CaseStatus.ASSIGNED.value,
        CaseStatus.INVESTIGATED.value,
        CaseStatus.ACTION_TAKEN.value,
        CaseStatus.RESOLUTION_PROPOSED.value,
        CaseStatus.CANCELLED.value,
    ],
    CaseStatus.DUPLICATE.value: [],
    CaseStatus.CANCELLED.value: [],
}


class CaseService:
    @staticmethod
    def generate_case_number(db: Session) -> str:
        """Generate human-readable sequential case number: MC-YYYY-XXXXX."""
        current_year = datetime.datetime.now(datetime.timezone.utc).year
        prefix = f"MC-{current_year}-"

        # Count cases created this year to determine sequence
        count = db.query(func.count(Case.id)).filter(Case.case_number.like(f"{prefix}%")).scalar() or 0
        sequence = count + 1
        return f"{prefix}{sequence:04d}"

    @staticmethod
    def log_timeline(
        db: Session,
        case_id: int,
        action: str,
        actor_id: Optional[int] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        notes: Optional[str] = None,
        is_internal: bool = False,
    ) -> CaseTimeline:
        timeline_entry = CaseTimeline(
            case_id=case_id,
            actor_id=actor_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            notes=notes,
            is_internal=is_internal,
        )
        db.add(timeline_entry)
        db.commit()
        db.refresh(timeline_entry)
        return timeline_entry

    @staticmethod
    def create_case(db: Session, case_in: CaseCreate, citizen_id: int) -> Case:
        case_number = CaseService.generate_case_number(db)

        # Auto-resolve department from category if provided
        dept_id = case_in.department_id
        if not dept_id and case_in.category_id:
            category = db.query(Category).filter(Category.id == case_in.category_id).first()
            if category:
                dept_id = category.department_id

        case_obj = Case(
            case_number=case_number,
            title=case_in.title.strip(),
            description=case_in.description.strip(),
            status=CaseStatus.REPORTED.value,
            priority=case_in.priority.value if case_in.priority else CasePriority.MEDIUM.value,
            severity=case_in.severity.value if case_in.severity else CaseSeverity.MODERATE.value,
            citizen_id=citizen_id,
            department_id=dept_id,
            category_id=case_in.category_id,
            ward=case_in.ward.strip() if case_in.ward else None,
            landmark=case_in.landmark.strip() if case_in.landmark else None,
            address=case_in.address.strip() if case_in.address else None,
            latitude=case_in.latitude,
            longitude=case_in.longitude,
        )
        db.add(case_obj)
        db.commit()
        db.refresh(case_obj)

        # Log creation in timeline
        CaseService.log_timeline(
            db,
            case_id=case_obj.id,
            action="CASE_CREATED",
            actor_id=citizen_id,
            new_value=case_obj.status,
            notes=f"Complaint registered by citizen. Case Number: {case_number}",
            is_internal=False,
        )

        # Log creation in central immutable AuditLog
        audit_service.log_event(
            db=db,
            action="CASE_CREATED",
            resource_type="case",
            resource_id=str(case_obj.id),
            actor_id=citizen_id,
            details=f"Citizen filed complaint {case_number}: '{case_obj.title}' in {case_obj.ward or 'General'}",
            new_values={
                "case_number": case_number,
                "title": case_obj.title,
                "status": case_obj.status,
                "priority": case_obj.priority,
                "ward": case_obj.ward,
            },
            is_ai_action=False,
        )

        from app.services.notification_service import notification_service
        from app.models.notification import NotificationEventType

        notification_service.dispatch_case_event_notifications(
            db=db,
            case=case_obj,
            event_type=NotificationEventType.CASE_CREATED.value,
            title=f"Complaint Registered: {case_number}",
            message=f"Your complaint '{case_obj.title}' has been registered and queued for municipal triage.",
        )

        return case_obj

    @staticmethod
    def get_by_id(db: Session, case_id: int) -> Optional[Case]:
        return db.query(Case).filter(Case.id == case_id).first()

    @staticmethod
    def get_by_number(db: Session, case_number: str) -> Optional[Case]:
        return db.query(Case).filter(Case.case_number == case_number.strip()).first()

    @staticmethod
    def list_cases(
        db: Session,
        user: User,
        status: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        priority: Optional[str] = None,
        priorities: Optional[List[str]] = None,
        severity: Optional[str] = None,
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
        team_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
        citizen_id: Optional[int] = None,
        ward: Optional[str] = None,
        search: Optional[str] = None,
        created_from: Optional[datetime.datetime] = None,
        created_to: Optional[datetime.datetime] = None,
        is_overdue: Optional[bool] = None,
        is_at_risk: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[Case], int]:
        query = db.query(Case)

        # Enforce server-side Requester isolation: Requesters see only their own cases!
        if user.role == UserRole.REQUESTER.value:
            query = query.filter(Case.citizen_id == user.id)
        elif citizen_id is not None:
            query = query.filter(Case.citizen_id == citizen_id)

        # Status filtering (single or list)
        if statuses:
            query = query.filter(Case.status.in_(statuses))
        elif status:
            if "," in status:
                query = query.filter(Case.status.in_([s.strip() for s in status.split(",")]))
            else:
                query = query.filter(Case.status == status)

        # Priority filtering
        if priorities:
            query = query.filter(Case.priority.in_(priorities))
        elif priority:
            if "," in priority:
                query = query.filter(Case.priority.in_([p.strip() for p in priority.split(",")]))
            else:
                query = query.filter(Case.priority == priority)

        # Severity filtering
        if severity:
            query = query.filter(Case.severity == severity)

        # Organizational filters
        if department_id is not None:
            query = query.filter(Case.department_id == department_id)
        if category_id is not None:
            query = query.filter(Case.category_id == category_id)
        if team_id is not None:
            query = query.filter(Case.team_id == team_id)
        if assigned_to_id is not None:
            query = query.filter(Case.assigned_to_id == assigned_to_id)
        if ward:
            query = query.filter(Case.ward.ilike(f"%{ward.strip()}%"))

        # Date range filters
        if created_from:
            query = query.filter(Case.created_at >= created_from)
        if created_to:
            query = query.filter(Case.created_at <= created_to)

        # Overdue / At-risk joins with CaseSLA if requested
        if is_overdue is not None or is_at_risk is not None:
            query = query.outerjoin(CaseSLA, Case.id == CaseSLA.case_id)
            if is_overdue is True:
                now = datetime.datetime.now(datetime.timezone.utc)
                query = query.filter(
                    or_(
                        CaseSLA.status == SLAStatus.BREACHED.value,
                        (CaseSLA.resolution_deadline < now) & (Case.closed_at.is_(None)),
                    )
                )
            if is_at_risk is True:
                query = query.filter(CaseSLA.status == SLAStatus.AT_RISK.value)

        # Multi-attribute textual keyword search
        if search:
            term = f"%{search.strip()}%"
            query = query.outerjoin(User, Case.citizen_id == User.id).filter(
                or_(
                    Case.case_number.ilike(term),
                    Case.title.ilike(term),
                    Case.description.ilike(term),
                    Case.ward.ilike(term),
                    Case.landmark.ilike(term),
                    Case.address.ilike(term),
                    Case.resolution_notes.ilike(term),
                    User.full_name.ilike(term),
                    User.email.ilike(term),
                    User.phone_number.ilike(term),
                )
            )

        total = query.count()

        # Sorting logic
        order_col = Case.created_at
        if sort_by == "updated_at":
            order_col = Case.updated_at
        elif sort_by == "priority":
            order_col = Case.priority
        elif sort_by == "status":
            order_col = Case.status
        elif sort_by == "case_number":
            order_col = Case.case_number

        if sort_order.lower() == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()
        return items, total

    @staticmethod
    def validate_transition(current_status: str, new_status: str) -> bool:
        """Check if transition from current_status to new_status is allowed."""
        if current_status == new_status:
            return True
        allowed = VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed

    @staticmethod
    def update_case_status(
        db: Session,
        case_obj: Case,
        new_status: CaseStatus,
        actor: User,
        reason: Optional[str] = None,
        resolution_notes: Optional[str] = None,
    ) -> Case:
        old_status = case_obj.status
        target_status = new_status.value

        if not CaseService.validate_transition(old_status, target_status):
            raise ValueError(f"Invalid state transition from '{old_status}' to '{target_status}'.")

        case_obj.status = target_status
        if resolution_notes:
            case_obj.resolution_notes = resolution_notes

        if target_status in [CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value]:
            case_obj.closed_at = datetime.datetime.now(datetime.timezone.utc)
        elif target_status == CaseStatus.REOPENED.value:
            case_obj.closed_at = None

        db.add(case_obj)
        db.commit()
        db.refresh(case_obj)

        # Log transition in timeline
        action_name = "STATUS_UPDATED"
        if target_status == CaseStatus.RESOLUTION_PROPOSED.value:
            action_name = "RESOLUTION_PROPOSED"
        elif target_status == CaseStatus.ESCALATED.value:
            action_name = "CASE_ESCALATED"

        CaseService.log_timeline(
            db,
            case_id=case_obj.id,
            action=action_name,
            actor_id=actor.id,
            old_value=old_status,
            new_value=target_status,
            notes=reason or resolution_notes or f"Status changed from {old_status} to {target_status}",
            is_internal=False,
        )

        # Central Audit Log
        audit_service.log_event(
            db=db,
            action=f"STATUS_CHANGED_TO_{target_status.upper()}",
            resource_type="case",
            resource_id=str(case_obj.id),
            actor_id=actor.id,
            details=reason or resolution_notes or f"Status moved from {old_status} to {target_status}",
            old_values={"status": old_status},
            new_values={"status": target_status, "resolution_notes": resolution_notes},
            is_ai_action=False,
        )

        from app.services.notification_service import notification_service
        from app.models.notification import NotificationEventType

        event_type = NotificationEventType.STATUS_CHANGED.value
        if target_status == CaseStatus.RESOLUTION_PROPOSED.value:
            event_type = NotificationEventType.RESOLUTION_PROPOSED.value
            msg = f"Municipal staff proposed resolution for '{case_obj.title}'. Please verify and confirm."
        elif target_status in [CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value]:
            event_type = NotificationEventType.CLOSED.value
            msg = f"Case '{case_obj.title}' has been marked as {target_status}."
        elif target_status == CaseStatus.WAITING_INFO.value:
            event_type = NotificationEventType.INFORMATION_REQUESTED.value
            msg = f"Additional information requested for case '{case_obj.title}'."
        else:
            msg = f"Case '{case_obj.title}' status moved to {target_status.replace('_', ' ').title()}."

        notification_service.dispatch_case_event_notifications(
            db=db,
            case=case_obj,
            event_type=event_type,
            title=f"Case Status: {case_obj.case_number}",
            message=msg,
            exclude_user_id=actor.id,
        )

        return case_obj

    @staticmethod
    def update_assignment(
        db: Session,
        case_obj: Case,
        actor: User,
        assigned_to_id: Optional[int] = None,
        team_id: Optional[int] = None,
        department_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Case:
        old_assignee = case_obj.assigned_to_id
        old_team = case_obj.team_id
        old_dept = case_obj.department_id

        if assigned_to_id is not None:
            case_obj.assigned_to_id = assigned_to_id
        if team_id is not None:
            case_obj.team_id = team_id
        if department_id is not None:
            case_obj.department_id = department_id

        # Auto advance status to ASSIGNED if currently reported or understood
        if (assigned_to_id is not None or team_id is not None) and case_obj.status in [CaseStatus.REPORTED.value, CaseStatus.UNDERSTOOD.value]:
            case_obj.status = CaseStatus.ASSIGNED.value

        db.add(case_obj)
        db.commit()
        db.refresh(case_obj)

        notes = reason or f"Case assigned to operator ID {assigned_to_id}"
        CaseService.log_timeline(
            db,
            case_id=case_obj.id,
            action="CASE_ASSIGNED",
            actor_id=actor.id,
            old_value=f"Assignee: {old_assignee}, Team: {old_team}, Dept: {old_dept}",
            new_value=f"Assignee: {case_obj.assigned_to_id}, Team: {case_obj.team_id}, Dept: {case_obj.department_id}",
            notes=notes,
            is_internal=False,
        )

        # Central Audit Log
        audit_service.log_event(
            db=db,
            action="CASE_REASSIGNED",
            resource_type="case",
            resource_id=str(case_obj.id),
            actor_id=actor.id,
            details=notes,
            old_values={"assigned_to_id": old_assignee, "team_id": old_team, "department_id": old_dept},
            new_values={"assigned_to_id": case_obj.assigned_to_id, "team_id": case_obj.team_id, "department_id": case_obj.department_id},
            is_ai_action=False,
        )

        from app.services.notification_service import notification_service
        from app.models.notification import NotificationEventType

        notification_service.dispatch_case_event_notifications(
            db=db,
            case=case_obj,
            event_type=NotificationEventType.ASSIGNMENT.value,
            title=f"Case Assigned: {case_obj.case_number}",
            message=f"Case '{case_obj.title}' has been assigned to operations team.",
            exclude_user_id=actor.id,
        )

        return case_obj

    @staticmethod
    def confirm_resolution(db: Session, case_obj: Case, citizen: User, notes: Optional[str] = None) -> Case:
        if case_obj.citizen_id != citizen.id and citizen.role != UserRole.ADMINISTRATOR.value:
            raise PermissionError("Only the citizen who reported this case can confirm resolution.")

        if case_obj.status != CaseStatus.RESOLUTION_PROPOSED.value:
            raise ValueError("Resolution can only be confirmed when case is in 'resolution_proposed' state.")

        old_status = case_obj.status
        case_obj.status = CaseStatus.CONFIRMED.value
        case_obj.closed_at = datetime.datetime.now(datetime.timezone.utc)

        db.add(case_obj)
        db.commit()
        db.refresh(case_obj)

        CaseService.log_timeline(
            db,
            case_id=case_obj.id,
            action="RESOLUTION_CONFIRMED",
            actor_id=citizen.id,
            old_value=old_status,
            new_value=CaseStatus.CONFIRMED.value,
            notes=notes or "Citizen verified and confirmed satisfactory resolution.",
            is_internal=False,
        )

        audit_service.log_event(
            db=db,
            action="RESOLUTION_CONFIRMED",
            resource_type="case",
            resource_id=str(case_obj.id),
            actor_id=citizen.id,
            details=notes or "Citizen verified and confirmed satisfactory resolution.",
            old_values={"status": old_status},
            new_values={"status": CaseStatus.CONFIRMED.value},
            is_ai_action=False,
        )

        from app.services.notification_service import notification_service
        from app.models.notification import NotificationEventType

        notification_service.dispatch_case_event_notifications(
            db=db,
            case=case_obj,
            event_type=NotificationEventType.CONFIRMED.value,
            title=f"Resolution Confirmed: {case_obj.case_number}",
            message=f"Citizen confirmed satisfactory resolution for case '{case_obj.title}'.",
            exclude_user_id=citizen.id,
        )

        return case_obj

    @staticmethod
    def reject_resolution(db: Session, case_obj: Case, citizen: User, rejection_reason: str) -> Case:
        if case_obj.citizen_id != citizen.id and citizen.role != UserRole.ADMINISTRATOR.value:
            raise PermissionError("Only the citizen who reported this case can reject resolution.")

        if case_obj.status != CaseStatus.RESOLUTION_PROPOSED.value:
            raise ValueError("Resolution can only be rejected when case is in 'resolution_proposed' state.")

        old_status = case_obj.status
        case_obj.status = CaseStatus.REOPENED.value
        case_obj.rejection_reason = rejection_reason.strip()
        case_obj.closed_at = None

        db.add(case_obj)
        db.commit()
        db.refresh(case_obj)

        CaseService.log_timeline(
            db,
            case_id=case_obj.id,
            action="RESOLUTION_REJECTED",
            actor_id=citizen.id,
            old_value=old_status,
            new_value=CaseStatus.REOPENED.value,
            notes=f"Citizen rejected resolution. Reason: {rejection_reason.strip()}",
            is_internal=False,
        )

        audit_service.log_event(
            db=db,
            action="RESOLUTION_REJECTED",
            resource_type="case",
            resource_id=str(case_obj.id),
            actor_id=citizen.id,
            details=f"Citizen rejected resolution. Reason: {rejection_reason.strip()}",
            old_values={"status": old_status},
            new_values={"status": CaseStatus.REOPENED.value, "rejection_reason": rejection_reason.strip()},
            is_ai_action=False,
        )

        from app.services.notification_service import notification_service
        from app.models.notification import NotificationEventType

        notification_service.dispatch_case_event_notifications(
            db=db,
            case=case_obj,
            event_type=NotificationEventType.REOPENED.value,
            title=f"Case Reopened: {case_obj.case_number}",
            message=f"Citizen rejected proposed resolution. Reason: {rejection_reason.strip()}",
            exclude_user_id=citizen.id,
        )

        return case_obj

    @staticmethod
    def get_unified_case_timeline(
        db: Session,
        case_id: int,
        user: User,
    ) -> UnifiedTimelineResponse:
        """
        Consolidates and returns a unified, chronological timeline of all activities,
        milestones, messages, notes, tasks, investigations, and escalations.
        Strictly enforces Requester Privacy Isolation (no internal notes/details leaked).
        """
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("Case not found.")

        # Requester isolation check
        is_requester = (user.role == UserRole.REQUESTER.value)
        if is_requester and case.citizen_id != user.id:
            raise PermissionError("You are not authorized to view this case timeline.")

        timeline_items: List[UnifiedTimelineItem] = []

        # 1. Base Case Lifecycle Events from CaseTimeline
        timelines = db.query(CaseTimeline).filter(CaseTimeline.case_id == case_id).all()
        for t in timelines:
            if is_requester and t.is_internal:
                continue
            actor_name = t.actor.full_name if t.actor else "System Automated"
            actor_role = t.actor.role if t.actor else "system"
            timeline_items.append(
                UnifiedTimelineItem(
                    id=f"timeline_{t.id}",
                    event_type="status_change" if "STATUS" in t.action else t.action.lower(),
                    title=t.action.replace("_", " ").title(),
                    description=t.notes,
                    actor_id=t.actor_id,
                    actor_name=actor_name,
                    actor_role=actor_role,
                    is_internal=t.is_internal,
                    metadata={"old_value": t.old_value, "new_value": t.new_value},
                    timestamp=t.created_at,
                )
            )

        # 2. Case Messages (Citizen & Staff public communications)
        messages = db.query(CaseMessage).filter(CaseMessage.case_id == case_id).all()
        for m in messages:
            timeline_items.append(
                UnifiedTimelineItem(
                    id=f"msg_{m.id}",
                    event_type="citizen_message" if m.is_from_citizen else "staff_update",
                    title="Citizen Response" if m.is_from_citizen else "Municipal Staff Update",
                    description=m.message,
                    actor_id=m.sender_id,
                    actor_name=m.sender.full_name if m.sender else "Staff",
                    actor_role=m.sender.role if m.sender else "staff",
                    is_internal=False,
                    metadata={"message_type": m.message_type},
                    timestamp=m.created_at,
                )
            )

        # 3. Internal Notes (Only for Staff / Admin)
        if not is_requester:
            internal_notes = db.query(InternalNote).filter(InternalNote.case_id == case_id).all()
            for note in internal_notes:
                timeline_items.append(
                    UnifiedTimelineItem(
                        id=f"note_{note.id}",
                        event_type="internal_note",
                        title=f"Internal Note ({note.note_type.title()})",
                        description=note.note,
                        actor_id=note.author_id,
                        actor_name=note.author.full_name if note.author else "Staff",
                        actor_role=note.author.role if note.author else "operator",
                        is_internal=True,
                        metadata={"note_type": note.note_type},
                        timestamp=note.created_at,
                    )
                )


        # 4. Field Tasks (Public or Staff)
        tasks = db.query(CaseTask).filter(CaseTask.case_id == case_id).all()
        for tk in tasks:
            timeline_items.append(
                UnifiedTimelineItem(
                    id=f"task_{tk.id}",
                    event_type=f"task_{tk.status}",
                    title=f"Field Task: {tk.title}",
                    description=f"Status: {tk.status.upper()}" + (f" | Assignee: {tk.assigned_to.full_name}" if tk.assigned_to else ""),
                    actor_id=tk.assigned_to_id,
                    actor_name=tk.assigned_to.full_name if tk.assigned_to else None,
                    actor_role=tk.assigned_to.role if tk.assigned_to else None,
                    is_internal=False,
                    metadata={"task_status": tk.status, "is_completed": tk.status == "completed"},
                    timestamp=tk.updated_at or tk.created_at,
                )
            )

        # 5. Field Investigations (Staff only)
        if not is_requester:
            investigations = db.query(CaseInvestigation).filter(CaseInvestigation.case_id == case_id).all()
            for inv in investigations:
                timeline_items.append(
                    UnifiedTimelineItem(
                        id=f"inv_{inv.id}",
                        event_type="investigation",
                        title="On-Site Field Investigation Recorded",
                        description=f"Observations: {inv.observations}" + (f" | Findings: {inv.findings}" if inv.findings else ""),
                        actor_id=inv.investigator_id,
                        actor_name=inv.investigator.full_name if inv.investigator else "Investigator",
                        actor_role=inv.investigator.role if inv.investigator else "operator",
                        is_internal=True,
                        metadata={"follow_up_requirements": inv.follow_up_requirements},
                        timestamp=inv.created_at,
                    )
                )


        # 6. Escalations
        escalations = db.query(CaseEscalation).filter(CaseEscalation.case_id == case_id).all()
        for esc in escalations:
            trigger_val = getattr(esc, "trigger_type", getattr(esc, "trigger", "manual")) or "manual"
            esc_actor = getattr(esc, "escalated_to", None) or getattr(esc, "assigned_to", None)
            timeline_items.append(
                UnifiedTimelineItem(
                    id=f"esc_{esc.id}",
                    event_type="escalation",
                    title=f"SLA Escalation ({esc.status.upper()})",
                    description=f"Trigger: {trigger_val.replace('_', ' ').title()}. Reason: {esc.reason}",
                    actor_id=esc.escalated_to_id if hasattr(esc, "escalated_to_id") else getattr(esc, "assigned_to_id", None),
                    actor_name=esc_actor.full_name if esc_actor else "Escalation Lead",
                    actor_role=esc_actor.role if esc_actor else "team_lead",
                    is_internal=False,
                    metadata={"escalation_status": esc.status, "trigger": trigger_val},
                    timestamp=esc.created_at,
                )
            )

        # 7. Attachments
        attachments = db.query(CaseAttachment).filter(CaseAttachment.case_id == case_id).all()
        for att in attachments:
            timeline_items.append(
                UnifiedTimelineItem(
                    id=f"att_{att.id}",
                    event_type="attachment",
                    title=f"Evidence Attached: {att.original_filename}",
                    description=f"File Type: {att.content_type} ({att.file_size // 1024} KB)",
                    actor_id=att.uploader_id,
                    actor_name=att.uploader.full_name if att.uploader else "User",
                    actor_role=att.uploader.role if att.uploader else "user",
                    is_internal=False,
                    metadata={"file_name": att.original_filename, "size_bytes": att.file_size},
                    timestamp=att.created_at,
                )
            )

        # Sort all timeline items chronologically (oldest to newest)
        timeline_items.sort(key=lambda item: item.timestamp, reverse=False)

        return UnifiedTimelineResponse(
            case_id=case.id,
            case_number=case.case_number,
            total_events=len(timeline_items),
            timeline=timeline_items,
        )


case_service = CaseService()
