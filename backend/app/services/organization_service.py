from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.organization import Department, Team, Category
from app.models.user import UserRole
from app.schemas.organization import (
    DepartmentCreate,
    DepartmentUpdate,
    TeamCreate,
    TeamUpdate,
    CategoryCreate,
    CategoryUpdate,
    PermissionDescriptor,
)


class OrganizationService:
    # --- Department Operations ---
    @staticmethod
    def list_departments(db: Session, active_only: bool = True) -> List[Department]:
        query = db.query(Department)
        if active_only:
            query = query.filter(Department.is_active.is_(True))
        return query.order_by(Department.name.asc()).all()

    @staticmethod
    def get_department_by_id(db: Session, department_id: int) -> Optional[Department]:
        return db.query(Department).filter(Department.id == department_id).first()

    @staticmethod
    def get_department_by_code(db: Session, code: str) -> Optional[Department]:
        return db.query(Department).filter(Department.code == code.upper().strip()).first()

    @staticmethod
    def create_department(db: Session, dept_in: DepartmentCreate) -> Department:
        dept = Department(
            name=dept_in.name.strip(),
            code=dept_in.code.upper().strip(),
            description=dept_in.description.strip() if dept_in.description else None,
            is_active=dept_in.is_active,
        )
        db.add(dept)
        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def update_department(db: Session, dept: Department, dept_in: DepartmentUpdate) -> Department:
        update_data = dept_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dept, field, value)
        db.add(dept)
        db.commit()
        db.refresh(dept)
        return dept

    # --- Team Operations ---
    @staticmethod
    def list_teams(db: Session, department_id: Optional[int] = None, active_only: bool = True) -> List[Team]:
        query = db.query(Team)
        if department_id is not None:
            query = query.filter(Team.department_id == department_id)
        if active_only:
            query = query.filter(Team.is_active.is_(True))
        return query.order_by(Team.name.asc()).all()

    @staticmethod
    def get_team_by_id(db: Session, team_id: int) -> Optional[Team]:
        return db.query(Team).filter(Team.id == team_id).first()

    @staticmethod
    def create_team(db: Session, team_in: TeamCreate) -> Team:
        team = Team(
            name=team_in.name.strip(),
            department_id=team_in.department_id,
            leader_id=team_in.leader_id,
            is_active=team_in.is_active,
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def update_team(db: Session, team: Team, team_in: TeamUpdate) -> Team:
        update_data = team_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    # --- Category Operations ---
    @staticmethod
    def list_categories(db: Session, department_id: Optional[int] = None, active_only: bool = True) -> List[Category]:
        query = db.query(Category)
        if department_id is not None:
            query = query.filter(Category.department_id == department_id)
        if active_only:
            query = query.filter(Category.is_active.is_(True))
        return query.order_by(Category.name.asc()).all()

    @staticmethod
    def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
        return db.query(Category).filter(Category.id == category_id).first()

    @staticmethod
    def get_category_by_code(db: Session, code: str) -> Optional[Category]:
        return db.query(Category).filter(Category.code == code.upper().strip()).first()

    @staticmethod
    def create_category(db: Session, cat_in: CategoryCreate) -> Category:
        category = Category(
            name=cat_in.name.strip(),
            code=cat_in.code.upper().strip(),
            department_id=cat_in.department_id,
            default_priority=cat_in.default_priority,
            sla_hours=cat_in.sla_hours,
            is_active=cat_in.is_active,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def update_category(db: Session, category: Category, cat_in: CategoryUpdate) -> Category:
        update_data = cat_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    # --- Role Permission Descriptor ---
    @staticmethod
    def get_role_permissions(role: str) -> PermissionDescriptor:
        is_admin = role == UserRole.ADMINISTRATOR.value
        is_manager = role == UserRole.MANAGER.value
        is_lead = role == UserRole.TEAM_LEAD.value
        is_operator = role == UserRole.OPERATOR.value
        is_requester = role == UserRole.REQUESTER.value

        return PermissionDescriptor(
            role=role,
            can_create_case=is_requester or is_operator or is_admin,
            can_view_all_cases=is_admin or is_manager or is_lead or is_operator,
            can_assign_cases=is_admin or is_manager or is_lead or is_operator,
            can_add_internal_notes=is_admin or is_manager or is_lead or is_operator,
            can_submit_resolution=is_admin or is_operator or is_lead,
            can_confirm_resolution=is_requester,
            can_escalate_case=is_admin or is_manager or is_lead or is_operator,
            can_manage_users=is_admin,
            can_manage_departments=is_admin,
            can_view_manager_analytics=is_admin or is_manager,
        )


organization_service = OrganizationService()
