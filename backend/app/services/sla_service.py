from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.case import Case, CasePriority, CaseStatus
from app.models.organization import Category
from app.models.sla import CaseSLA, SLAStatus
from app.schemas.sla import CaseSLAResponse


def calculate_sla_targets(category_sla_hours: int, priority: str) -> Tuple[int, int]:
    """
    Calculate response and resolution target hours based on category baseline SLA and priority.
    """
    baseline = max(4, category_sla_hours)
    priority_str = (priority or "medium").lower()

    if priority_str == CasePriority.CRITICAL.value:
        response_hours = max(1, baseline // 12)
        resolution_hours = max(4, baseline // 4)
    elif priority_str == CasePriority.HIGH.value:
        response_hours = max(2, baseline // 6)
        resolution_hours = max(8, baseline // 2)
    elif priority_str == CasePriority.LOW.value:
        response_hours = max(8, baseline // 2)
        resolution_hours = int(baseline * 1.5)
    else:  # MEDIUM default
        response_hours = max(4, baseline // 4)
        resolution_hours = baseline

    return response_hours, resolution_hours


def format_time_remaining(
    created_at: datetime,
    due_at: datetime,
    completed_at: Optional[datetime] = None,
) -> Tuple[str, float]:
    """
    Returns human-friendly plain language text and progress percentage (0-100%).
    """
    now = datetime.now(timezone.utc)
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    total_window_seconds = max(1.0, (due_at - created_at).total_seconds())

    if completed_at is not None:
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)
        if completed_at <= due_at:
            return "Met on time", 100.0
        else:
            diff = completed_at - due_at
            diff_hours = int(diff.total_seconds() // 3600)
            diff_mins = int((diff.total_seconds() % 3600) // 60)
            if diff_hours > 24:
                days = diff_hours // 24
                return f"Breached by {days}d {diff_hours % 24}h", 100.0
            elif diff_hours > 0:
                return f"Breached by {diff_hours}h {diff_mins}m", 100.0
            else:
                return f"Breached by {diff_mins}m", 100.0

    # Active countdown
    if now > due_at:
        diff = now - due_at
        diff_hours = int(diff.total_seconds() // 3600)
        diff_mins = int((diff.total_seconds() % 3600) // 60)
        if diff_hours >= 24:
            days = diff_hours // 24
            return f"Breached by {days}d {diff_hours % 24}h", 100.0
        elif diff_hours > 0:
            return f"Breached by {diff_hours}h {diff_mins}m", 100.0
        else:
            return f"Breached by {diff_mins}m", 100.0
    else:
        remaining = due_at - now
        elapsed = (now - created_at).total_seconds()
        progress = min(100.0, max(0.0, (elapsed / total_window_seconds) * 100.0))

        rem_hours = int(remaining.total_seconds() // 3600)
        rem_mins = int((remaining.total_seconds() % 3600) // 60)

        if rem_hours >= 24:
            days = rem_hours // 24
            hours_left = rem_hours % 24
            return f"{days}d {hours_left}h remaining", progress
        elif rem_hours > 0:
            return f"{rem_hours}h {rem_mins}m remaining", progress
        else:
            return f"{rem_mins}m remaining", progress


def initialize_or_update_case_sla(db: Session, case: Case, force_recalc: bool = False) -> CaseSLA:
    """
    Initializes or recalculates SLA deadlines for a case.
    """
    category_sla_hours = 48
    if case.category_id:
        cat = db.query(Category).filter(Category.id == case.category_id).first()
        if cat and cat.sla_hours:
            category_sla_hours = cat.sla_hours

    resp_hours, res_hours = calculate_sla_targets(category_sla_hours, case.priority)

    sla = db.query(CaseSLA).filter(CaseSLA.case_id == case.id).first()
    now = datetime.now(timezone.utc)
    base_time = case.created_at or now
    if base_time.tzinfo is None:
        base_time = base_time.replace(tzinfo=timezone.utc)

    if not sla:
        sla = CaseSLA(
            case_id=case.id,
            response_target_hours=resp_hours,
            resolution_target_hours=res_hours,
            response_due_at=base_time + timedelta(hours=resp_hours),
            resolution_due_at=base_time + timedelta(hours=res_hours),
            response_status=SLAStatus.WITHIN_TARGET.value,
            resolution_status=SLAStatus.WITHIN_TARGET.value,
            is_breached=False,
        )
        db.add(sla)
        db.commit()
        db.refresh(sla)
    elif force_recalc:
        sla.response_target_hours = resp_hours
        sla.resolution_target_hours = res_hours
        sla.response_due_at = base_time + timedelta(hours=resp_hours)
        sla.resolution_due_at = base_time + timedelta(hours=res_hours)
        db.commit()
        db.refresh(sla)

    # Evaluate dynamic status
    return evaluate_single_case_sla(db, case, sla)


def evaluate_single_case_sla(
    db: Session, case: Case, sla: Optional[CaseSLA] = None
) -> CaseSLA:
    """
    Evaluates current time against SLA targets and updates breach/warning status.
    """
    if not sla:
        sla = db.query(CaseSLA).filter(CaseSLA.case_id == case.id).first()
        if not sla:
            return initialize_or_update_case_sla(db, case)

    now = datetime.now(timezone.utc)
    res_due = sla.resolution_due_at
    if res_due.tzinfo is None:
        res_due = res_due.replace(tzinfo=timezone.utc)
    resp_due = sla.response_due_at
    if resp_due.tzinfo is None:
        resp_due = resp_due.replace(tzinfo=timezone.utc)

    # 1. Evaluate Response Target
    responded_statuses = {
        CaseStatus.UNDERSTOOD.value,
        CaseStatus.ASSIGNED.value,
        CaseStatus.INVESTIGATED.value,
        CaseStatus.ACTION_TAKEN.value,
        CaseStatus.RESOLUTION_PROPOSED.value,
        CaseStatus.CONFIRMED.value,
        CaseStatus.CLOSED.value,
    }

    if case.status in responded_statuses:
        if not sla.first_responded_at:
            sla.first_responded_at = now
        sla.response_status = (
            SLAStatus.MET.value
            if sla.first_responded_at <= resp_due
            else SLAStatus.BREACHED.value
        )
    else:
        if now > resp_due:
            sla.response_status = SLAStatus.BREACHED.value
        elif (resp_due - now).total_seconds() <= (sla.response_target_hours * 3600 * 0.25):
            sla.response_status = SLAStatus.APPROACHING_BREACH.value
        else:
            sla.response_status = SLAStatus.WITHIN_TARGET.value

    # 2. Evaluate Resolution Target
    resolved_statuses = {
        CaseStatus.RESOLUTION_PROPOSED.value,
        CaseStatus.CONFIRMED.value,
        CaseStatus.CLOSED.value,
    }

    if case.status in resolved_statuses:
        if not sla.resolved_at:
            sla.resolved_at = now
        sla.resolution_status = (
            SLAStatus.MET.value
            if sla.resolved_at <= res_due
            else SLAStatus.BREACHED.value
        )
    else:
        # Case still active / open
        sla.resolved_at = None
        if now > res_due:
            sla.resolution_status = SLAStatus.BREACHED.value
            sla.is_breached = True
            if not sla.breached_at:
                sla.breached_at = now
        elif (res_due - now).total_seconds() <= (sla.resolution_target_hours * 3600 * 0.25):
            sla.resolution_status = SLAStatus.APPROACHING_BREACH.value
        else:
            sla.resolution_status = SLAStatus.WITHIN_TARGET.value

    # Global breach flag
    if sla.response_status == SLAStatus.BREACHED.value or sla.resolution_status == SLAStatus.BREACHED.value:
        sla.is_breached = True
        if not sla.breached_at:
            sla.breached_at = now
    else:
        sla.is_breached = False

    db.commit()
    db.refresh(sla)
    return sla


def build_case_sla_response(sla: CaseSLA) -> CaseSLAResponse:
    """
    Transforms a CaseSLA record into a full UI response with formatted plain text countdowns.
    """
    created_at = sla.created_at or datetime.now(timezone.utc)
    resp_text, resp_prog = format_time_remaining(
        created_at=created_at,
        due_at=sla.response_due_at,
        completed_at=sla.first_responded_at,
    )
    res_text, res_prog = format_time_remaining(
        created_at=created_at,
        due_at=sla.resolution_due_at,
        completed_at=sla.resolved_at,
    )

    return CaseSLAResponse(
        id=sla.id,
        case_id=sla.case_id,
        response_target_hours=sla.response_target_hours,
        resolution_target_hours=sla.resolution_target_hours,
        response_due_at=sla.response_due_at,
        resolution_due_at=sla.resolution_due_at,
        first_responded_at=sla.first_responded_at,
        resolved_at=sla.resolved_at,
        response_status=sla.response_status,
        resolution_status=sla.resolution_status,
        is_breached=sla.is_breached,
        breached_at=sla.breached_at,
        warning_issued_at=sla.warning_issued_at,
        created_at=sla.created_at,
        response_remaining_text=resp_text,
        resolution_remaining_text=res_text,
        response_progress_percentage=round(resp_prog, 1),
        resolution_progress_percentage=round(res_prog, 1),
    )
