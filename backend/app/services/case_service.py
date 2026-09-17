import datetime
from typing import List, Optional, Tuple
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from app.models.case import Case, CaseTimeline, CaseStatus, CasePriority, CaseSeverity
from app.models.organization import Category
from app.models.user import User, UserRole
from app.schemas.case import CaseCreate, CaseUpdate, CaseStatusUpdate, CaseAssignmentUpdate


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
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
        ward: Optional[str] = None,
        assigned_to_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[Case], int]:
        query = db.query(Case)

        # Enforce server-side Requester isolation: Requesters see only their own cases!
        if user.role == UserRole.REQUESTER.value:
            query = query.filter(Case.citizen_id == user.id)

        if status:
            query = query.filter(Case.status == status)
        if department_id is not None:
            query = query.filter(Case.department_id == department_id)
        if category_id is not None:
            query = query.filter(Case.category_id == category_id)
        if ward:
            query = query.filter(Case.ward.ilike(f"%{ward}%"))
        if assigned_to_id is not None:
            query = query.filter(Case.assigned_to_id == assigned_to_id)

        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Case.case_number.ilike(term),
                    Case.title.ilike(term),
                    Case.description.ilike(term),
                    Case.ward.ilike(term),
                    Case.landmark.ilike(term),
                )
            )

        total = query.count()
        offset = (page - 1) * size
        items = query.order_by(Case.created_at.desc()).offset(offset).limit(size).all()
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
            # Auto advance status to ASSIGNED if currently reported or understood
            if case_obj.status in [CaseStatus.REPORTED.value, CaseStatus.UNDERSTOOD.value]:
                case_obj.status = CaseStatus.ASSIGNED.value

        if team_id is not None:
            case_obj.team_id = team_id
        if department_id is not None:
            case_obj.department_id = department_id

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
        return case_obj


case_service = CaseService()
