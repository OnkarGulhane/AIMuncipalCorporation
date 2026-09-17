import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import SessionLocal
from app.models.case import Case, CaseStatus

from app.models.sla import SLAStatus
from app.schemas.escalation import EscalationCreate
from app.services.sla_service import evaluate_single_case_sla
from app.services.risk_service import evaluate_case_risk
from app.services.escalation_service import create_case_escalation

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def sweep_slas_and_risks_sync():
    """
    Synchronous worker routine executed by APScheduler job.
    Scans active civic cases for SLA deadlines and risk conditions.
    """
    db = SessionLocal()
    try:
        active_statuses = [
            CaseStatus.REPORTED.value,
            CaseStatus.UNDERSTOOD.value,
            CaseStatus.ASSIGNED.value,
            CaseStatus.INVESTIGATED.value,
            CaseStatus.ACTION_TAKEN.value,
            CaseStatus.WAITING_INFO.value,
            CaseStatus.ESCALATED.value,
            CaseStatus.REOPENED.value,
        ]

        active_cases = db.query(Case).filter(Case.status.in_(active_statuses)).all()
        now = datetime.now(timezone.utc)

        for case in active_cases:
            try:
                # 1. Evaluate SLA status
                sla = evaluate_single_case_sla(db, case)

                # 2. Check for SLA breach escalation
                if sla.is_breached or sla.resolution_status == SLAStatus.BREACHED.value:
                    if not case.is_escalated:
                        create_case_escalation(
                            db=db,
                            case=case,
                            escalation_data=EscalationCreate(
                                reason="Automated SLA Breach: Case resolution target deadline has passed.",
                                trigger_type="sla_breach",
                            ),
                            current_user=None,
                        )

                # 3. Evaluate operational risk
                risk = evaluate_case_risk(db, case)
                if risk.risk_tier == "critical" and not case.is_escalated:
                    create_case_escalation(
                        db=db,
                        case=case,
                        escalation_data=EscalationCreate(
                            reason=f"Automated Risk Alert: Case reached Critical Risk score ({risk.risk_score}/100). Primary factor: {risk.risk_factors[0]}",
                            trigger_type="risk_threshold",
                        ),
                        current_user=None,
                    )
            except Exception as e:
                logger.error(f"Error evaluating SLA/Risk for case {case.id}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error during SLA and Risk sweep: {e}")
    finally:
        db.close()


async def sweep_slas_and_risks():
    sweep_slas_and_risks_sync()


def start_scheduler():
    """Starts the in-process APScheduler background tasks."""
    if not scheduler.running:
        scheduler.add_job(
            sweep_slas_and_risks,
            trigger=IntervalTrigger(seconds=60),
            id="sla_and_risk_sweep",
            name="Periodic SLA and Risk Evaluation Sweep",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler initialized and running SLA/Risk sweep every 60s.")


def shutdown_scheduler():
    """Gracefully shuts down APScheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down successfully.")
