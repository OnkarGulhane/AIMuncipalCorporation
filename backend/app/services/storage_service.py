from typing import List, Tuple, Optional
import pathlib
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.storage import storage_manager
from app.models.user import User, UserRole
from app.models.case import Case, CaseTimeline
from app.models.attachment import CaseAttachment
from app.schemas.attachment import CaseAttachmentResponse


class StorageService:
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
                detail="You do not have permission to access attachments for this case.",
            )
        return case

    @staticmethod
    async def upload_attachment(
        db: Session,
        case_id: int,
        file: UploadFile,
        user: User,
        description: Optional[str] = None,
        is_public_to_citizen: bool = True,
    ) -> CaseAttachmentResponse:
        case = StorageService._get_case_with_access(db, case_id, user)

        # Save binary file safely to disk
        stored_filename, relative_path, file_size = await storage_manager.save_file(
            file=file, case_id=case_id
        )

        attachment = CaseAttachment(
            case_id=case_id,
            uploaded_by_id=user.id,
            original_filename=file.filename or stored_filename,
            stored_filename=stored_filename,
            file_path=relative_path,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            description=description,
            is_public_to_citizen=is_public_to_citizen,
        )
        db.add(attachment)

        # Timeline event
        timeline_entry = CaseTimeline(
            case_id=case_id,
            actor_id=user.id,
            action="attachment_uploaded",
            notes=f"Attached file: {attachment.original_filename} ({file_size // 1024} KB){f' - {description}' if description else ''}",
            is_internal=not is_public_to_citizen,
        )
        db.add(timeline_entry)

        db.commit()
        db.refresh(attachment)

        return CaseAttachmentResponse(
            id=attachment.id,
            case_id=attachment.case_id,
            uploaded_by_id=attachment.uploaded_by_id,
            uploaded_by_name=user.full_name,
            uploaded_by_role=user.role,
            original_filename=attachment.original_filename,
            file_size=attachment.file_size,
            content_type=attachment.content_type,
            description=attachment.description,
            is_public_to_citizen=attachment.is_public_to_citizen,
            created_at=attachment.created_at,
        )

    @staticmethod
    def list_attachments(
        db: Session, case_id: int, user: User
    ) -> List[CaseAttachmentResponse]:
        StorageService._get_case_with_access(db, case_id, user)

        query = db.query(CaseAttachment).filter(CaseAttachment.case_id == case_id)
        if user.role == UserRole.REQUESTER:
            query = query.filter(CaseAttachment.is_public_to_citizen == True)

        attachments = query.order_by(CaseAttachment.created_at.desc()).all()

        results = []
        for att in attachments:
            results.append(
                CaseAttachmentResponse(
                    id=att.id,
                    case_id=att.case_id,
                    uploaded_by_id=att.uploaded_by_id,
                    uploaded_by_name=att.uploaded_by.full_name if att.uploaded_by else None,
                    uploaded_by_role=att.uploaded_by.role if att.uploaded_by else None,
                    original_filename=att.original_filename,
                    file_size=att.file_size,
                    content_type=att.content_type,
                    description=att.description,
                    is_public_to_citizen=att.is_public_to_citizen,
                    created_at=att.created_at,
                )
            )
        return results

    @staticmethod
    def get_attachment_for_download(
        db: Session, case_id: int, attachment_id: int, user: User
    ) -> Tuple[CaseAttachment, pathlib.Path]:
        StorageService._get_case_with_access(db, case_id, user)

        attachment = (
            db.query(CaseAttachment)
            .filter(CaseAttachment.id == attachment_id, CaseAttachment.case_id == case_id)
            .first()
        )
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attachment with ID {attachment_id} not found on this case.",
            )

        if user.role == UserRole.REQUESTER and not attachment.is_public_to_citizen:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this internal staff attachment.",
            )

        abs_path = storage_manager.get_absolute_path(attachment.file_path)
        return attachment, abs_path

    @staticmethod
    def delete_attachment(
        db: Session, case_id: int, attachment_id: int, user: User
    ) -> bool:
        StorageService._get_case_with_access(db, case_id, user)

        attachment = (
            db.query(CaseAttachment)
            .filter(CaseAttachment.id == attachment_id, CaseAttachment.case_id == case_id)
            .first()
        )
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attachment with ID {attachment_id} not found.",
            )

        # Only uploader, Admin, or Manager can delete attachment
        if user.role == UserRole.REQUESTER and attachment.uploaded_by_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete attachments that you uploaded.",
            )

        storage_manager.delete_file(attachment.file_path)
        db.delete(attachment)
        db.commit()
        return True


storage_service = StorageService()
