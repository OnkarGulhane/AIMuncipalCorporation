import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Set
from sqlalchemy.orm import Session

from app.models.case import Case, CaseStatus
from app.models.user import User, UserRole
from app.models.notification import (
    Notification,
    NotificationPreference,
    NotificationEventType,
    NotificationChannel,
)
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class NotificationService:
    def get_or_create_preferences(self, db: Session, user_id: int) -> NotificationPreference:
        prefs = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if not prefs:
            prefs = NotificationPreference(
                user_id=user_id,
                email_enabled=True,
                in_app_enabled=True,
                notify_on_assignment=True,
                notify_on_status_change=True,
                notify_on_sla_warning=True,
                notify_on_escalation=True,
                notify_on_messages=True,
            )
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        return prefs

    def update_preferences(
        self, db: Session, user_id: int, updates: NotificationPreferenceUpdate
    ) -> NotificationPreference:
        prefs = self.get_or_create_preferences(db, user_id)
        update_data = updates.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(prefs, key, val)
        db.commit()
        db.refresh(prefs)
        return prefs

    def create_notification(
        self,
        db: Session,
        user_id: int,
        title: str,
        message: str,
        event_type: str = NotificationEventType.STATUS_CHANGED.value,
        case_id: Optional[int] = None,
        channel: str = NotificationChannel.IN_APP.value,
        send_email_if_enabled: bool = True,
    ) -> Notification:
        """
        Creates an in-app notification record and dispatches email if enabled in preferences.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"Cannot create notification for non-existent user_id {user_id}")
            return None

        prefs = self.get_or_create_preferences(db, user_id)

        # Respect user preferences based on event type
        if not prefs.in_app_enabled:
            return None

        if event_type == NotificationEventType.ASSIGNMENT.value and not prefs.notify_on_assignment:
            return None
        if event_type in {NotificationEventType.SLA_WARNING.value} and not prefs.notify_on_sla_warning:
            return None
        if event_type in {NotificationEventType.ESCALATION.value, NotificationEventType.ESCALATION_RESOLVED.value} and not prefs.notify_on_escalation:
            return None
        if event_type in {NotificationEventType.CITIZEN_RESPONSE.value, NotificationEventType.STAFF_UPDATE.value} and not prefs.notify_on_messages:
            return None

        # Create in-app record
        notification = Notification(
            user_id=user_id,
            case_id=case_id,
            title=title,
            message=message,
            event_type=event_type,
            channel=channel,
            is_read=False,
            delivery_status="delivered",
            email_sent=False,
            email_to=user.email,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Dispatch email if enabled
        if send_email_if_enabled and prefs.email_enabled and user.email:
            case = db.query(Case).filter(Case.id == case_id).first() if case_id else None
            case_num = case.case_number if case else "Civic Notification"
            case_title = case.title if case else title

            subj, text_b, html_b = email_service.format_case_email(
                case_number=case_num,
                case_title=case_title,
                event_title=title,
                event_message=message,
                recipient_name=user.full_name or "Citizen",
            )
            email_sent = email_service.send_transactional_email(
                to_email=user.email,
                subject=subj,
                text_body=text_b,
                html_body=html_b,
                event_type=event_type,
            )
            if email_sent:
                notification.email_sent = True
                db.commit()

        return notification

    def dispatch_case_event_notifications(
        self,
        db: Session,
        case: Case,
        event_type: str,
        title: str,
        message: str,
        exclude_user_id: Optional[int] = None,
    ) -> List[Notification]:
        """
        Dispatches targeted notifications to relevant roles according to PRD Section 43 matrix.
        """
        recipients: Set[int] = set()

        # 1. Citizen Recipient
        citizen_events = {
            NotificationEventType.CASE_CREATED.value,
            NotificationEventType.STATUS_CHANGED.value,
            NotificationEventType.STAFF_UPDATE.value,
            NotificationEventType.INFORMATION_REQUESTED.value,
            NotificationEventType.RESOLUTION_PROPOSED.value,
            NotificationEventType.CONFIRMED.value,
            NotificationEventType.CLOSED.value,
            NotificationEventType.REOPENED.value,
        }
        if event_type in citizen_events and case.citizen_id:
            recipients.add(case.citizen_id)

        # 2. Assigned Operator Recipient
        operator_events = {
            NotificationEventType.ASSIGNMENT.value,
            NotificationEventType.CITIZEN_RESPONSE.value,
            NotificationEventType.TASK_ASSIGNED.value,
            NotificationEventType.SLA_WARNING.value,
            NotificationEventType.ESCALATION.value,
            NotificationEventType.REOPENED.value,
        }
        if event_type in operator_events and case.assigned_to_id:
            recipients.add(case.assigned_to_id)

        # 3. Team Lead Recipient
        team_lead_events = {
            NotificationEventType.ESCALATION.value,
            NotificationEventType.ESCALATION_RESOLVED.value,
            NotificationEventType.SLA_WARNING.value,
            NotificationEventType.REOPENED.value,
        }
        if event_type in team_lead_events:
            # Find team leads for department/team
            lead_users = (
                db.query(User)
                .filter(User.role.in_([UserRole.TEAM_LEAD.value, UserRole.MANAGER.value]))
                .all()
            )
            for u in lead_users:
                if case.department_id and u.department_id == case.department_id:
                    recipients.add(u.id)
                elif u.role == UserRole.MANAGER.value:
                    recipients.add(u.id)

        # Remove excluded actor
        if exclude_user_id and exclude_user_id in recipients:
            recipients.remove(exclude_user_id)

        created_notifications = []
        for uid in recipients:
            notif = self.create_notification(
                db=db,
                user_id=uid,
                title=title,
                message=message,
                event_type=event_type,
                case_id=case.id,
            )
            if notif:
                created_notifications.append(notif)

        return created_notifications

    def list_user_notifications(
        self,
        db: Session,
        user_id: int,
        unread_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> NotificationListResponse:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)

        total = query.count()
        unread_count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .count()
        )

        items = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

        return NotificationListResponse(
            items=[self.build_notification_response(n) for n in items],
            total=total,
            unread_count=unread_count,
            page=(offset // limit) + 1,
            size=limit,
        )

    def get_unread_count(self, db: Session, user_id: int) -> int:
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .count()
        )

    def mark_notification_as_read(
        self, db: Session, notification_id: int, user_id: int
    ) -> Optional[Notification]:
        notif = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if notif:
            notif.is_read = True
            notif.read_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(notif)
        return notif

    def mark_all_notifications_as_read(self, db: Session, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({"is_read": True, "read_at": now})
        )
        db.commit()
        return count

    def delete_notification(self, db: Session, notification_id: int, user_id: int) -> bool:
        notif = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if notif:
            db.delete(notif)
            db.commit()
            return True
        return False

    def build_notification_response(self, notif: Notification) -> NotificationResponse:
        return NotificationResponse(
            id=notif.id,
            user_id=notif.user_id,
            case_id=notif.case_id,
            case_number=notif.case_rel.case_number if notif.case_rel else None,
            case_title=notif.case_rel.title if notif.case_rel else None,
            title=notif.title,
            message=notif.message,
            event_type=notif.event_type,
            channel=notif.channel,
            is_read=notif.is_read,
            read_at=notif.read_at,
            delivery_status=notif.delivery_status,
            created_at=notif.created_at,
        )


notification_service = NotificationService()
