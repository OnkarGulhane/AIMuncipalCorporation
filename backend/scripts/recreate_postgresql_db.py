"""
Recreate & Clean Seed PostgreSQL Database: ai_muncipal_db
Password: OMKAR7778
"""
import sys
import os

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

DB_USER = "postgres"
DB_PASS = "OMKAR7778"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "ai_muncipal_db"

def recreate_database():
    print("=" * 70)
    print("POSTGRESQL CLEAN RESET & RECREATION")
    print("=" * 70)

    # 1. Connect to root postgres database
    print(f"1. Connecting to PostgreSQL server on {DB_HOST}:{DB_PORT} as {DB_USER}...")
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # 2. Terminate active sessions on ai_muncipal_db
    print(f"2. Terminating active sessions on database '{DB_NAME}'...")
    cur.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{DB_NAME}'
          AND pid <> pg_backend_pid();
    """)

    # 3. Drop existing database
    print(f"3. Dropping database '{DB_NAME}' if exists...")
    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")

    # 4. Create clean database
    print(f"4. Creating fresh database '{DB_NAME}'...")
    cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};")
    cur.close()
    conn.close()
    print("[SUCCESS] Fresh PostgreSQL database created successfully!")

    # 5. Import all model modules so Base.metadata knows all tables
    print("5. Loading all ORM model definitions...")
    from app.core.database import Base, engine, SessionLocal
    import app.models.user
    import app.models.organization
    import app.models.case
    import app.models.activity
    import app.models.attachment
    import app.models.sla
    import app.models.escalation
    import app.models.ai_analysis
    import app.models.audit
    import app.models.notification

    # Create all tables in the fresh database
    Base.metadata.create_all(bind=engine)
    print("[SUCCESS] All 18 relational tables created in PostgreSQL.")

    # 6. Seed demo data
    print("6. Seeding 5 role accounts, departments, categories, teams, and sample cases...")
    from scripts.seed_demo_data import seed_demo_database
    db = SessionLocal()
    try:
        seed_demo_database(db=db)
    finally:
        db.close()

    print("=" * 70)
    print("[SUCCESS] POSTGRESQL DATABASE RESET & DEMO SEEDING COMPLETE WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    recreate_database()
