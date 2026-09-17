import json
import logging
from typing import Optional, List, Tuple, Any, Dict
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        actor_id: Optional[int] = None,
        details: Optional[str] = None,
        old_values: Optional[Any] = None,
        new_values: Optional[Any] = None,
        ip_address: Optional[str] = None,
        is_ai_action: bool = False,
    ) -> AuditLog:
        """
        Record an immutable audit log entry for human, AI, or system operations.
        """
        try:
            # Format dictionaries to JSON strings if passed
            old_val_str = json.dumps(old_values) if isinstance(old_values, dict) else (str(old_values) if old_values is not None else None)
            new_val_str = json.dumps(new_values) if isinstance(new_values, dict) else (str(new_values) if new_values is not None else None)

            entry = AuditLog(
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id is not None else None,
                details=details,
                old_values=old_val_str,
                new_values=new_val_str,
                ip_address=ip_address,
                is_ai_action=is_ai_action,
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")
            db.rollback()
            # Return transient object if commit failed so core flow is never blocked
            return AuditLog(
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id is not None else None,
                details=details,
                is_ai_action=is_ai_action,
            )

    @staticmethod
    def list_logs(
        db: Session,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        actor_id: Optional[int] = None,
        action: Optional[str] = None,
        is_ai_action: Optional[bool] = None,
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[AuditLog], int]:
        query = db.query(AuditLog)

        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == str(resource_id))
        if actor_id is not None:
            query = query.filter(AuditLog.actor_id == actor_id)
        if action:
            query = query.filter(AuditLog.action.ilike(f"%{action}%"))
        if is_ai_action is not None:
            query = query.filter(AuditLog.is_ai_action == is_ai_action)

        total = query.count()
        offset = (page - 1) * size
        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(size).all()
        return logs, total

    @staticmethod
    def get_case_audit_trail(db: Session, case_id: int) -> List[AuditLog]:
        return (
            db.query(AuditLog)
            .filter(
                (AuditLog.resource_type == "case") & (AuditLog.resource_id == str(case_id))
            )
            .order_by(AuditLog.created_at.desc())
            .all()
        )


audit_service = AuditService()
