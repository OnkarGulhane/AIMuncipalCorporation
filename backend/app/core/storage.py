import os
import uuid
import pathlib
import shutil
from typing import Tuple, Set
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

ALLOWED_EXTENSIONS: Set[str] = {
    # Images
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg",
    # Documents
    ".pdf", ".txt", ".csv", ".doc", ".docx", ".xls", ".xlsx",
    # Videos / Media
    ".mp4", ".mov", ".avi", ".webm",
}

ALLOWED_MIME_PREFIXES: Tuple[str, ...] = (
    "image/",
    "application/pdf",
    "text/",
    "video/",
    "application/msword",
    "application/vnd.openxmlformats-officedocument",
)


class StorageManager:
    def __init__(self, base_dir: str = settings.UPLOAD_DIR):
        self.base_dir = pathlib.Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile) -> None:
        """Validate filename, extension, and content type."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a valid filename.",
            )

        ext = pathlib.Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' is not supported. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        content_type = file.content_type or ""
        if not any(content_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES):
            # If content type is generic octet-stream, allow if extension is permitted
            if content_type != "application/octet-stream":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Content type '{content_type}' is not supported for case evidence.",
                )

    async def save_file(self, file: UploadFile, case_id: int) -> Tuple[str, str, int]:
        """
        Save file to disk in a case-scoped subdirectory.
        Returns: (stored_filename, relative_file_path, file_size_bytes)
        """
        self.validate_file(file)

        # Create case-specific folder
        case_dir = self.base_dir / f"case_{case_id}"
        case_dir.mkdir(parents=True, exist_ok=True)

        # Generate safe stored filename
        ext = pathlib.Path(file.filename).suffix.lower()
        unique_id = uuid.uuid4().hex[:12]
        safe_orig_name = "".join(c for c in pathlib.Path(file.filename).stem if c.isalnum() or c in ("-", "_"))[:30]
        stored_filename = f"{unique_id}_{safe_orig_name}{ext}"

        dest_path = case_dir / stored_filename

        # Read and write with size limit checking
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        file_size = 0

        try:
            with open(dest_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):  # 1MB chunks
                    file_size += len(chunk)
                    if file_size > max_bytes:
                        # Clean up partial file
                        buffer.close()
                        if dest_path.exists():
                            dest_path.unlink()
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.",
                        )
                    buffer.write(chunk)
        finally:
            await file.seek(0)

        # Store path relative to base upload directory
        relative_path = str(pathlib.Path(f"case_{case_id}") / stored_filename).replace("\\", "/")

        return stored_filename, relative_path, file_size

    def get_absolute_path(self, relative_path: str) -> pathlib.Path:
        """Resolve and verify path is safely inside the upload base directory."""
        clean_rel = relative_path.replace("\\", "/").strip("/")
        abs_path = (self.base_dir / clean_rel).resolve()

        if not str(abs_path).startswith(str(self.base_dir)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path detected.",
            )

        if not abs_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical file was not found on storage disk.",
            )

        return abs_path

    def delete_file(self, relative_path: str) -> bool:
        """Safely remove a file from disk."""
        try:
            abs_path = self.get_absolute_path(relative_path)
            if abs_path.exists():
                abs_path.unlink()
                return True
        except Exception:
            pass
        return False


storage_manager = StorageManager()
