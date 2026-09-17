from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_active_user
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    UnreadCountResponse,
)
from app.services.notification_service import notification_service

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List in-app notifications for the authenticated user with optional unread filter and pagination.
    """
    offset = (page - 1) * size
    return notification_service.list_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        offset=offset,
        limit=size,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get the count of unread notifications for the active user badge counter.
    """
    count = notification_service.get_unread_count(db=db, user_id=current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Mark a single notification as read.
    """
    notif = notification_service.mark_notification_as_read(
        db=db, notification_id=notification_id, user_id=current_user.id
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found or does not belong to you.",
        )
    return notification_service.build_notification_response(notif)


@router.post("/mark-all-read")
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Mark all unread notifications for the current user as read.
    """
    count = notification_service.mark_all_notifications_as_read(db=db, user_id=current_user.id)
    return {"status": "success", "marked_read_count": count}


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve notification preferences for the authenticated user.
    """
    prefs = notification_service.get_or_create_preferences(db=db, user_id=current_user.id)
    return NotificationPreferenceResponse.model_validate(prefs)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_notification_preferences(
    updates: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update notification channels and event toggles for the authenticated user.
    """
    prefs = notification_service.update_preferences(db=db, user_id=current_user.id, updates=updates)
    return NotificationPreferenceResponse.model_validate(prefs)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete a notification.
    """
    deleted = notification_service.delete_notification(
        db=db, notification_id=notification_id, user_id=current_user.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found or does not belong to you.",
        )
    return None
