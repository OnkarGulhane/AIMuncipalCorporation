import enum
from sqlalchemy import Column, String, Boolean, Enum
from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    REQUESTER = "requester"
    OPERATOR = "operator"
    TEAM_LEAD = "team_lead"
    MANAGER = "manager"
    ADMINISTRATOR = "administrator"


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=True)
    role = Column(
        String(50),
        default=UserRole.REQUESTER.value,
        index=True,
        nullable=False,
    )
    department = Column(String(100), nullable=True)
    ward = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
