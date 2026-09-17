from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CaseAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    uploaded_by_id: int
    uploaded_by_name: Optional[str] = None
    uploaded_by_role: Optional[str] = None
    original_filename: str
    file_size: int
    content_type: str
    description: Optional[str] = None
    is_public_to_citizen: bool
    created_at: datetime
