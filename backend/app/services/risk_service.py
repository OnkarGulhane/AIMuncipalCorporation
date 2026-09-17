from datetime import datetime, timezone
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.case import Case, CaseStatus, CasePriority, CaseSeverity, CaseTimeline
from app.models.activity import CaseMessage
from app.models.sla import CaseSLA, SLAStatus
from app.schemas.sla import RiskAnalysisResponse, RiskSignalItem
from app.services.sla_service import evaluate_single_case_sla


def evaluate_case_risk(db: Session, case: Case) -> RiskAnalysisResponse:
    """
    Evaluates multi-factor operational and SLA risk signals for a civic case.
    """
    signals: List[RiskSignalItem] = []
    risk_factors: List[str] = []
    score = 0
    now = datetime.now(timezone.utc)

    # Make sure SLA is evaluated first
    sla = db.query(CaseSLA).filter(CaseSLA.case_id == case.id).first()
    if not sla:
        sla = evaluate_single_case_sla(db, case)
    else:
        sla = evaluate_single_case_sla(db, case, sla)

    # 1. SLA Breach / Approaching Breach Signal
    if sla.is_breached or sla.resolution_status == SLAStatus.BREACHED.value:
        score += 35
        risk_factors.append("Resolution SLA deadline has been breached.")
        signals.append(
            RiskSignalItem(
                key="sla_breach",
                label="SLA Breached",
                severity="critical",
                description="The maximum resolution time target for this category and priority has passed.",
            )
        )
    elif sla.resolution_status == SLAStatus.APPROACHING_BREACH.value or sla.response_status == SLAStatus.APPROACHING_BREACH.value:
        score += 18
        risk_factors.append("SLA deadline is rapidly approaching (<25% time remaining).")
        signals.append(
            RiskSignalItem(
                key="sla_approaching",
                label="Approaching SLA Deadline",
                severity="high",
                description="Less than 25% of the allocated target time remains for resolution/response.",
            )
        )

    # 2. Inactivity Signal (> 24 hours on active cases)
    terminal_statuses = {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value, CaseStatus.CANCELLED.value}
    if case.status not in terminal_statuses:
        latest_timeline = (
            db.query(CaseTimeline)
            .filter(CaseTimeline.case_id == case.id)
            .order_by(CaseTimeline.created_at.desc())
            .first()
        )
        last_action_time = latest_timeline.created_at if latest_timeline else case.created_at
        if last_action_time:
            if last_action_time.tzinfo is None:
                last_action_time = last_action_time.replace(tzinfo=timezone.utc)
            inactive_hours = int((now - last_action_time).total_seconds() // 3600)
            if inactive_hours >= 48:
                score += 25
                risk_factors.append(f"Case has been inactive for {inactive_hours} hours without updates.")
                signals.append(
                    RiskSignalItem(
                        key="high_inactivity",
                        label="Prolonged Inactivity",
                        severity="high",
                        description=f"No activity or status changes recorded for over {inactive_hours} hours.",
                    )
                )
            elif inactive_hours >= 24:
                score += 15
                risk_factors.append(f"No staff updates or actions recorded in the last {inactive_hours} hours.")
                signals.append(
                    RiskSignalItem(
                        key="inactivity",
                        label="Inactivity Alert",
                        severity="medium",
                        description="Case has not progressed for over 24 hours.",
                    )
                )

    # 3. Repeated Citizen Follow-ups / Messages Signal
    citizen_messages_count = (
        db.query(CaseMessage)
        .filter(
            CaseMessage.case_id == case.id,
            CaseMessage.sender_id == case.citizen_id,
        )
        .count()
    )
    if citizen_messages_count >= 3:
        score += 20
        risk_factors.append(f"Citizen has sent {citizen_messages_count} follow-up inquiries.")
        signals.append(
            RiskSignalItem(
                key="repeated_followups",
                label="Frequent Follow-ups",
                severity="high",
                description=f"Citizen has inquired {citizen_messages_count} times regarding lack of resolution.",
            )
        )
    elif citizen_messages_count >= 2:
        score += 10
        risk_factors.append("Citizen has submitted multiple follow-up messages.")
        signals.append(
            RiskSignalItem(
                key="citizen_followups",
                label="Citizen Follow-up",
                severity="medium",
                description="Citizen is actively checking in on status.",
            )
        )

    # 4. Multiple Reassignments / Organizational Ping-Pong
    reassignments_count = (
        db.query(CaseTimeline)
        .filter(
            CaseTimeline.case_id == case.id,
            CaseTimeline.action.in_(["assigned", "reassigned", "team_changed"]),
        )
        .count()
    )
    if reassignments_count >= 3:
        score += 20
        risk_factors.append(f"Case has been reassigned {reassignments_count} times across staff/teams.")
        signals.append(
            RiskSignalItem(
                key="excessive_reassignments",
                label="Department Ping-Pong",
                severity="high",
                description="Multiple reassignments indicate ambiguity in ownership or jurisdiction.",
            )
        )
    elif reassignments_count == 2:
        score += 10
        risk_factors.append("Case has undergone multiple assignment changes.")
        signals.append(
            RiskSignalItem(
                key="multiple_assignments",
                label="Reassigned Case",
                severity="medium",
                description="Case has changed assignees more than once.",
            )
        )

    # 5. Reopened Case Signal
    reopen_count = (
        db.query(CaseTimeline)
        .filter(
            CaseTimeline.case_id == case.id,
            CaseTimeline.action == "reopened",
        )
        .count()
    )
    if case.status == CaseStatus.REOPENED.value or reopen_count > 0:
        score += 25
        risk_factors.append(f"Citizen rejected resolution; case reopened ({reopen_count} time(s)).")
        signals.append(
            RiskSignalItem(
                key="reopened_case",
                label="Rejected Resolution",
                severity="high",
                description="Prior resolution attempt failed citizen verification.",
            )
        )

    # 6. Severity & Safety Hazards
    if case.priority == CasePriority.CRITICAL.value or case.severity == CaseSeverity.CRITICAL.value:
        score += 20
        risk_factors.append("Critical safety or public hazard classification.")
        signals.append(
            RiskSignalItem(
                key="critical_hazard",
                label="Critical Priority",
                severity="critical",
                description="Immediate public safety risk or major service disruption.",
            )
        )
    elif case.priority == CasePriority.HIGH.value or case.severity == CaseSeverity.MAJOR.value:
        score += 10
        risk_factors.append("High priority municipal issue.")
        signals.append(
            RiskSignalItem(
                key="high_priority",
                label="High Priority",
                severity="medium",
                description="High priority civic grievance requiring fast turnaround.",
            )
        )

    # 7. Missing Information / Unassigned
    if not case.assigned_to_id and case.status not in terminal_statuses:
        score += 10
        risk_factors.append("Case is currently unassigned to an operator.")
        signals.append(
            RiskSignalItem(
                key="unassigned",
                label="Unassigned Case",
                severity="medium",
                description="No staff member is currently accountable for this case.",
            )
        )

    # Normalize score
    final_score = min(100, score)

    # Determine tier
    if final_score >= 70:
        tier = "critical"
    elif final_score >= 45:
        tier = "high"
    elif final_score >= 20:
        tier = "medium"
    else:
        tier = "low"

    if not risk_factors:
        risk_factors.append("No active risk factors detected. Progressing within expected parameters.")

    return RiskAnalysisResponse(
        case_id=case.id,
        risk_score=final_score,
        risk_tier=tier,
        risk_factors=risk_factors,
        signals=signals,
        evaluated_at=now,
    )
