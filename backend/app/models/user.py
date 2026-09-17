import enum
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
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
    department = Column(String(100), nullable=True)  # Legacy string representation
    department_id = Column(
        Integer,
        ForeignKey("departments.id", name="fk_users_department_id", use_alter=True),
        nullable=True,
    )
    team_id = Column(
        Integer,
        ForeignKey("teams.id", name="fk_users_team_id", use_alter=True),
        nullable=True,
    )
    ward = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)

    department_rel = relationship("Department", foreign_keys=[department_id], back_populates="users")
    team_rel = relationship("Team", foreign_keys=[team_id], back_populates="members")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
