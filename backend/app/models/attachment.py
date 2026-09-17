from sqlalchemy import Column, String, Boolean, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CaseAttachment(BaseModel):
    __tablename__ = "case_attachments"

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    content_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_public_to_citizen = Column(Boolean, default=True, nullable=False)

    case_rel = relationship("Case", foreign_keys=[case_id], back_populates="attachments")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])

    def __repr__(self) -> str:
        return f"<CaseAttachment {self.original_filename} ({self.file_size} bytes) on Case {self.case_id}>"
