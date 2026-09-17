from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.services.storage_service import storage_service
from app.schemas.attachment import CaseAttachmentResponse

router = APIRouter()


@router.post(
    "/{case_id}/attachments",
    response_model=CaseAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload evidence or document attachment for a case",
)
async def upload_case_attachment(
    case_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    is_public_to_citizen: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload photos, documents, or video evidence for a case.
    Saves binary safely to disk storage and registers metadata in database.
    """
    return await storage_service.upload_attachment(
        db,
        case_id=case_id,
        file=file,
        user=current_user,
        description=description,
        is_public_to_citizen=is_public_to_citizen,
    )


@router.get(
    "/{case_id}/attachments",
    response_model=List[CaseAttachmentResponse],
    summary="List all attachments/evidence for a case",
)
def list_case_attachments(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve metadata for all files attached to the case."""
    return storage_service.list_attachments(
        db, case_id=case_id, user=current_user
    )


@router.get(
    "/{case_id}/attachments/{attachment_id}/download",
    summary="Download or stream case attachment file",
)
def download_case_attachment(
    case_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Stream binary file to client with proper Content-Disposition and MIME type."""
    attachment, abs_path = storage_service.get_attachment_for_download(
        db, case_id=case_id, attachment_id=attachment_id, user=current_user
    )

    return FileResponse(
        path=str(abs_path),
        filename=attachment.original_filename,
        media_type=attachment.content_type,
    )


@router.delete(
    "/{case_id}/attachments/{attachment_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an attachment",
)
def delete_case_attachment(
    case_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an attachment and remove its physical file from storage."""
    storage_service.delete_attachment(
        db, case_id=case_id, attachment_id=attachment_id, user=current_user
    )
    return {"message": "Attachment deleted successfully."}
