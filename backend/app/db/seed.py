import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal
from app.core.logging import logger
from app.models.user import UserRole
from app.schemas.organization import DepartmentCreate, TeamCreate, CategoryCreate
from app.schemas.user import UserCreate
from app.services.organization_service import organization_service
from app.services.user_service import user_service

DEFAULT_DEPARTMENTS = [
    {
        "name": "Roads & Infrastructure",
        "code": "ROADS",
        "description": "Road maintenance, pothole patching, bridges, and pavement infrastructure.",
    },
    {
        "name": "Solid Waste Management",
        "code": "WASTE",
        "description": "Garbage collection, community bins, street sweeping, and sanitation.",
    },
    {
        "name": "Water Supply & Distribution",
        "code": "WATER",
        "description": "Drinking water pipelines, leakage repair, supply pressure, and water tankers.",
    },
    {
        "name": "Electrical & Street Lighting",
        "code": "ELECTRICAL",
        "description": "Streetlights, high-mast lamps, exposed cables, and municipal electrical fixtures.",
    },
    {
        "name": "Drainage & Stormwater",
        "code": "DRAINAGE",
        "description": "Underground sewer lines, stormwater drains, and open canal unclogging.",
    },
]

DEFAULT_CATEGORIES = [
    {
        "name": "Potholes & Road Damage",
        "code": "POTHOLES",
        "dept_code": "ROADS",
        "default_priority": "high",
        "sla_hours": 48,
    },
    {
        "name": "Garbage Dump & Waste Overflow",
        "code": "GARBAGE_OVERFLOW",
        "dept_code": "WASTE",
        "default_priority": "medium",
        "sla_hours": 24,
    },
    {
        "name": "Water Pipeline Leakage / Contamination",
        "code": "WATER_LEAKAGE",
        "dept_code": "WATER",
        "default_priority": "high",
        "sla_hours": 24,
    },
    {
        "name": "Streetlight Not Working / Dark Spot",
        "code": "STREETLIGHT_OUT",
        "dept_code": "ELECTRICAL",
        "default_priority": "medium",
        "sla_hours": 72,
    },
    {
        "name": "Blocked Drainage / Sewer Overflow",
        "code": "DRAINAGE_CLOG",
        "dept_code": "DRAINAGE",
        "default_priority": "high",
        "sla_hours": 36,
    },
    {
        "name": "Fallen Tree / Road Obstruction",
        "code": "FALLEN_TREE",
        "dept_code": "ROADS",
        "default_priority": "critical",
        "sla_hours": 12,
    },
]

DEMO_USERS = [
    {
        "email": "citizen@demo.com",
        "password": "Demo@1234",
        "full_name": "Aarav Sharma (Citizen)",
        "phone_number": "+91 9876543210",
        "role": UserRole.REQUESTER,
        "ward": "Ward 12 - Shivaji Nagar",
        "dept_code": None,
    },
    {
        "email": "operator@demo.com",
        "password": "Demo@1234",
        "full_name": "Rohan Deshmukh (Case Operator)",
        "phone_number": "+91 9876543211",
        "role": UserRole.OPERATOR,
        "ward": "Ward 12 - Shivaji Nagar",
        "dept_code": "ROADS",
    },
    {
        "email": "teamlead@demo.com",
        "password": "Demo@1234",
        "full_name": "Priya Patil (Team Lead)",
        "phone_number": "+91 9876543212",
        "role": UserRole.TEAM_LEAD,
        "ward": "Zone 4",
        "dept_code": "ROADS",
    },
    {
        "email": "manager@demo.com",
        "password": "Demo@1234",
        "full_name": "Vikram Kulkarni (Municipal Manager)",
        "phone_number": "+91 9876543213",
        "role": UserRole.MANAGER,
        "ward": "Municipal HQ",
        "dept_code": None,
    },
    {
        "email": "admin@demo.com",
        "password": "Demo@1234",
        "full_name": "Sneha Joshi (System Administrator)",
        "phone_number": "+91 9876543214",
        "role": UserRole.ADMINISTRATOR,
        "ward": "IT Department",
        "dept_code": None,
    },
]


def seed_database():
    """Seed departments, categories, teams, and safe demo accounts."""
    logger.info("Starting safe demo database seeding (Departments, Categories, Users)...")
    db = SessionLocal()

    try:
        # 1. Seed Departments
        dept_map = {}
        for dept_data in DEFAULT_DEPARTMENTS:
            existing = organization_service.get_department_by_code(db, code=dept_data["code"])
            if not existing:
                created = organization_service.create_department(
                    db,
                    dept_in=DepartmentCreate(
                        name=dept_data["name"],
                        code=dept_data["code"],
                        description=dept_data["description"],
                    ),
                )
                dept_map[dept_data["code"]] = created
                logger.info(f"Created department: {created.name} ({created.code})")
            else:
                dept_map[dept_data["code"]] = existing

        # 2. Seed Categories
        for cat_data in DEFAULT_CATEGORIES:
            existing = organization_service.get_category_by_code(db, code=cat_data["code"])
            if not existing and cat_data["dept_code"] in dept_map:
                dept = dept_map[cat_data["dept_code"]]
                created = organization_service.create_category(
                    db,
                    cat_in=CategoryCreate(
                        name=cat_data["name"],
                        code=cat_data["code"],
                        department_id=dept.id,
                        default_priority=cat_data["default_priority"],
                        sla_hours=cat_data["sla_hours"],
                    ),
                )
                logger.info(f"Created category: {created.name} (SLA: {created.sla_hours}h)")

        # 3. Seed Users
        for user_data in DEMO_USERS:
            existing = user_service.get_by_email(db, email=user_data["email"])
            dept_id = dept_map[user_data["dept_code"]].id if user_data.get("dept_code") and user_data["dept_code"] in dept_map else None

            if not existing:
                create_payload = UserCreate(
                    email=user_data["email"],
                    password=user_data["password"],
                    full_name=user_data["full_name"],
                    phone_number=user_data["phone_number"],
                    role=user_data["role"],
                    ward=user_data["ward"],
                    department=user_data.get("dept_code"),
                )
                created_user = user_service.create_user(
                    db,
                    user_in=create_payload,
                    forced_role=user_data["role"],
                )
                created_user.department_id = dept_id
                db.add(created_user)
                db.commit()
                logger.info(f"Created demo user: {user_data['email']} ({user_data['role'].value})")

        # 4. Seed Operational Team
        if "ROADS" in dept_map:
            roads_dept = dept_map["ROADS"]
            team_lead = user_service.get_by_email(db, email="teamlead@demo.com")
            operator = user_service.get_by_email(db, email="operator@demo.com")

            existing_teams = organization_service.list_teams(db, department_id=roads_dept.id)
            if not existing_teams:
                team = organization_service.create_team(
                    db,
                    team_in=TeamCreate(
                        name="Ward 12 Road Rapid Response Squad",
                        department_id=roads_dept.id,
                        leader_id=team_lead.id if team_lead else None,
                    ),
                )
                if operator:
                    operator.team_id = team.id
                    db.add(operator)
                    db.commit()
                logger.info(f"Created operational team: {team.name}")

        logger.info("Database seeding completed successfully.")
    except Exception as e:
        logger.error(f"Error during seeding: {str(e)}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
