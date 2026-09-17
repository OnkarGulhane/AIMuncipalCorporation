import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal, Base, engine
from app.core.logging import logger
from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.services.user_service import user_service

DEMO_USERS = [
    {
        "email": "citizen@demo.com",
        "password": "Demo@1234",
        "full_name": "Aarav Sharma (Citizen)",
        "phone_number": "+91 9876543210",
        "role": UserRole.REQUESTER,
        "ward": "Ward 12 - Shivaji Nagar",
        "department": None,
    },
    {
        "email": "operator@demo.com",
        "password": "Demo@1234",
        "full_name": "Rohan Deshmukh (Case Operator)",
        "phone_number": "+91 9876543211",
        "role": UserRole.OPERATOR,
        "ward": "Ward 12 - Shivaji Nagar",
        "department": "Roads & Infrastructure",
    },
    {
        "email": "teamlead@demo.com",
        "password": "Demo@1234",
        "full_name": "Priya Patil (Team Lead)",
        "phone_number": "+91 9876543212",
        "role": UserRole.TEAM_LEAD,
        "ward": "Zone 4",
        "department": "Public Works & Infrastructure",
    },
    {
        "email": "manager@demo.com",
        "password": "Demo@1234",
        "full_name": "Vikram Kulkarni (Municipal Manager)",
        "phone_number": "+91 9876543213",
        "role": UserRole.MANAGER,
        "ward": "Municipal HQ",
        "department": "Municipal Operations & Governance",
    },
    {
        "email": "admin@demo.com",
        "password": "Demo@1234",
        "full_name": "Sneha Joshi (System Administrator)",
        "phone_number": "+91 9876543214",
        "role": UserRole.ADMINISTRATOR,
        "ward": "IT Department",
        "department": "Administration & Security",
    },
]


def seed_database():
    """Seed safe demo accounts for local development and demonstration."""
    logger.info("Starting safe demo database seeding...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        created_count = 0
        for user_data in DEMO_USERS:
            existing = user_service.get_by_email(db, email=user_data["email"])
            if not existing:
                create_payload = UserCreate(
                    email=user_data["email"],
                    password=user_data["password"],
                    full_name=user_data["full_name"],
                    phone_number=user_data["phone_number"],
                    role=user_data["role"],
                    ward=user_data["ward"],
                    department=user_data["department"],
                )
                user_service.create_user(
                    db,
                    user_in=create_payload,
                    forced_role=user_data["role"],
                )
                logger.info(f"Created demo user: {user_data['email']} ({user_data['role'].value})")
                created_count += 1
            else:
                logger.info(f"Demo user already exists: {user_data['email']}")

        logger.info(f"Database seeding completed successfully. ({created_count} users created)")
    except Exception as e:
        logger.error(f"Error during seeding: {str(e)}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
