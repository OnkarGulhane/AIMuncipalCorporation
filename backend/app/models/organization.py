from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Department(BaseModel):
    __tablename__ = "departments"

    name = Column(String(100), unique=True, index=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    teams = relationship("Team", back_populates="department", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="department", cascade="all, delete-orphan")
    users = relationship("User", back_populates="department_rel", foreign_keys="User.department_id")

    def __repr__(self) -> str:
        return f"<Department {self.code} - {self.name}>"


class Team(BaseModel):
    __tablename__ = "teams"

    name = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    leader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    department = relationship("Department", back_populates="teams")
    leader = relationship("User", foreign_keys=[leader_id])
    members = relationship("User", back_populates="team_rel", foreign_keys="User.team_id")

    def __repr__(self) -> str:
        return f"<Team {self.name} (Dept: {self.department_id})>"


class Category(BaseModel):
    __tablename__ = "categories"

    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    default_priority = Column(String(20), default="medium", nullable=False)
    sla_hours = Column(Integer, default=48, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    department = relationship("Department", back_populates="categories")

    def __repr__(self) -> str:
        return f"<Category {self.code} - {self.name}>"
