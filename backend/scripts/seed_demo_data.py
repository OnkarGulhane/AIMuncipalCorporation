"""
AI Case Manager — Automated Municipal Demo Seeding Script
Populates the database with realistic municipal data, departments, categories,
5 role-ready demo accounts, cases across all lifecycle stages, and audit history.
"""

import sys
import os
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.organization import Department, Category, Team
from app.models.case import Case, CaseStatus, CasePriority, CaseSeverity
from app.models.activity import CaseMessage, InternalNote, CaseTask, CaseInvestigation, TaskStatus
from app.models.attachment import CaseAttachment
from app.models.sla import CaseSLA, SLAStatus
from app.models.escalation import CaseEscalation, EscalationStatus
from app.models.audit import AuditLog
from app.models.notification import Notification, NotificationPreference
from app.schemas.organization import DepartmentCreate, CategoryCreate, TeamCreate
from app.services.organization_service import organization_service
from app.services.ai_service import ai_service
from app.services.sla_service import evaluate_single_case_sla, calculate_sla_targets
from app.services.audit_service import audit_service


def seed_demo_database(db: Optional[Session] = None):
    print("=" * 70)
    print("AI Municipal Corporation — Initializing Realistic Demo Seed Data")
    print("=" * 70)

    close_session = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_session = True

    try:
        now = datetime.now(timezone.utc)

        # ---------------------------------------------------------------------
        # 1. Seed Municipal Departments
        # ---------------------------------------------------------------------
        print("[1/6] Seeding Municipal Departments...")
        dept_data = [
            {"name": "Public Works & Roads", "code": "ROADS", "description": "Road maintenance, asphalt resurfacing, bridge repairs and footpath maintenance"},
            {"name": "Water Supply & Drainage", "code": "WATER", "description": "Drinking water pipelines, sewer lines, stormwater drains, and pump stations"},
            {"name": "Solid Waste & Sanitation", "code": "SANITATION", "description": "Daily waste collection, street sweeping, bin clearance, and recycling centers"},
            {"name": "Electrical & Street Lighting", "code": "ELECTRICAL", "description": "Streetlights, high-mast lamps, power transformer maintenance, and safety wiring"},
            {"name": "Public Health & Pest Control", "code": "HEALTH", "description": "Vector-borne disease control, fogging, stray animal management, and sanitation hygiene"},
        ]

        departments = {}
        for d in dept_data:
            existing = db.query(Department).filter(Department.code == d["code"]).first()
            if not existing:
                dept = Department(name=d["name"], code=d["code"], description=d["description"], is_active=True)
                db.add(dept)
                db.commit()
                db.refresh(dept)
                departments[d["code"]] = dept
            else:
                departments[d["code"]] = existing

        # ---------------------------------------------------------------------
        # 2. Seed Civic Categories
        # ---------------------------------------------------------------------
        print("[2/6] Seeding Civic Complaint Categories & SLA Baselines...")
        cat_data = [
            {"name": "Pothole & Road Crater", "code": "POTHOLE", "dept": "ROADS", "sla_hours": 24},
            {"name": "Broken Footpath Concrete Slab", "code": "FOOTPATH", "dept": "ROADS", "sla_hours": 48},
            {"name": "Drinking Water Contamination", "code": "WATER_CONTAM", "dept": "WATER", "sla_hours": 12},
            {"name": "Underground Pipe Burst", "code": "PIPE_BURST", "dept": "WATER", "sla_hours": 8},
            {"name": "Overflowing Public Garbage Dump", "code": "GARBAGE_OVERFLOW", "dept": "SANITATION", "sla_hours": 12},
            {"name": "Dead Animal Carcass Removal", "code": "ANIMAL_REMOVAL", "dept": "SANITATION", "sla_hours": 6},
            {"name": "Street Light Not Functioning", "code": "STREET_LIGHT", "dept": "ELECTRICAL", "sla_hours": 24},
            {"name": "Exposed Sparking Live Cable", "code": "SPARKING_WIRE", "dept": "ELECTRICAL", "sla_hours": 4},
            {"name": "Mosquito Breeding & Fogging Request", "code": "FOGGING", "dept": "HEALTH", "sla_hours": 48},
            {"name": "Stray Dog Pack Aggression", "code": "STRAY_DOGS", "dept": "HEALTH", "sla_hours": 24},
        ]

        categories = {}
        for c in cat_data:
            existing = db.query(Category).filter(Category.code == c["code"]).first()
            dept_id = departments[c["dept"]].id
            if not existing:
                cat = Category(name=c["name"], code=c["code"], department_id=dept_id, sla_hours=c["sla_hours"], is_active=True)
                db.add(cat)
                db.commit()
                db.refresh(cat)
                categories[c["code"]] = cat
            else:
                categories[c["code"]] = existing

        # ---------------------------------------------------------------------
        # 3. Seed Municipal Field Squads / Teams
        # ---------------------------------------------------------------------
        print("[3/6] Seeding Municipal Field Squads...")
        team_data = [
            {"name": "Road Squad Alpha", "dept": "ROADS"},
            {"name": "Water Emergency Response Unit", "dept": "WATER"},
            {"name": "Rapid Sanitation Crew", "dept": "SANITATION"},
        ]

        teams = {}
        for t in team_data:
            dept_id = departments[t["dept"]].id
            existing = db.query(Team).filter(Team.name == t["name"], Team.department_id == dept_id).first()
            if not existing:
                team = Team(name=t["name"], department_id=dept_id, is_active=True)
                db.add(team)
                db.commit()
                db.refresh(team)
                teams[t["name"]] = team
            else:
                teams[t["name"]] = existing

        # ---------------------------------------------------------------------
        # 4. Seed 5 Role-Based Demo Users
        # ---------------------------------------------------------------------
        print("[4/6] Seeding 5 Role Demo Users (Password: Password123)...")
        default_pwd_hash = get_password_hash("Password123")

        user_configs = [
            {
                "email": "citizen@demo.city.gov",
                "full_name": "Rahul Deshmukh (Citizen)",
                "role": UserRole.REQUESTER.value,
                "ward": "Ward 12 - North",
                "phone_number": "+91 98765 43210",
                "department_id": None,
                "team_id": None,
            },
            {
                "email": "operator@demo.city.gov",
                "full_name": "Sanjay Field Operator",
                "role": UserRole.OPERATOR.value,
                "ward": "Ward 12 - North",
                "phone_number": "+91 98765 43211",
                "department_id": departments["ROADS"].id,
                "team_id": teams["Road Squad Alpha"].id,
            },
            {
                "email": "teamlead@demo.city.gov",
                "full_name": "Anjali Lead Engineer",
                "role": UserRole.TEAM_LEAD.value,
                "ward": "Ward 12 - North",
                "phone_number": "+91 98765 43212",
                "department_id": departments["ROADS"].id,
                "team_id": teams["Road Squad Alpha"].id,
            },
            {
                "email": "manager@demo.city.gov",
                "full_name": "Vikas Ward Commissioner",
                "role": UserRole.MANAGER.value,
                "ward": "Ward 12 - North",
                "phone_number": "+91 98765 43213",
                "department_id": departments["ROADS"].id,
                "team_id": None,
            },
            {
                "email": "admin@demo.city.gov",
                "full_name": "Chief Municipal Administrator",
                "role": UserRole.ADMINISTRATOR.value,
                "ward": "Ward 01 - Municipal HQ",
                "phone_number": "+91 98765 43214",
                "department_id": None,
                "team_id": None,
            },
        ]

        users = {}
        for u in user_configs:
            user = db.query(User).filter(User.email == u["email"]).first()
            if not user:
                user = User(
                    email=u["email"],
                    hashed_password=default_pwd_hash,
                    full_name=u["full_name"],
                    role=u["role"],
                    ward=u["ward"],
                    phone_number=u["phone_number"],
                    department_id=u["department_id"],
                    team_id=u["team_id"],
                    is_active=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                user.hashed_password = default_pwd_hash
                user.role = u["role"]
                user.ward = u["ward"]
                user.department_id = u["department_id"]
                user.team_id = u["team_id"]
                db.commit()
                db.refresh(user)

            # Notification preferences
            pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user.id).first()
            if not pref:
                db.add(NotificationPreference(user_id=user.id, in_app_enabled=True, email_enabled=True))
                db.commit()

            users[u["role"]] = user

        # ---------------------------------------------------------------------
        # 5. Seed Realistic Multi-State Civic Cases
        # ---------------------------------------------------------------------
        print("[5/6] Seeding Multi-State Civic Cases with Full Audit History...")
        cit = users[UserRole.REQUESTER.value]
        op = users[UserRole.OPERATOR.value]
        lead = users[UserRole.TEAM_LEAD.value]
        mgr = users[UserRole.MANAGER.value]
        adm = users[UserRole.ADMINISTRATOR.value]

        cases_to_seed = [
            # Case 1: Active Assigned Pothole Case
            {
                "case_number": "MC-2026-1001",
                "title": "Severe dangerous pothole outside Model High School",
                "description": "Large 1.2m pothole causing heavy congestion and near-accidents for school buses during morning hours.",
                "ward": "Ward 12 - North",
                "landmark": "Opposite Model High School Main Gate",
                "address": "MG Road, Sector 4",
                "status": CaseStatus.ASSIGNED.value,
                "priority": CasePriority.HIGH.value,
                "severity": CaseSeverity.MAJOR.value,
                "dept_code": "ROADS",
                "cat_code": "POTHOLE",
                "team_name": "Road Squad Alpha",
                "assigned_to": op,
                "created_ago_hours": 6,
            },
            # Case 2: Waiting for Citizen Clarification
            {
                "case_number": "MC-2026-1002",
                "title": "Drinking water pipeline contamination and foul smell",
                "description": "Muddy brown tap water supply since yesterday morning. Multiple households affected on 3rd Lane.",
                "ward": "Ward 12 - North",
                "landmark": "Near Community Hall",
                "address": "3rd Cross Lane, North Block",
                "status": CaseStatus.WAITING_INFO.value,
                "priority": CasePriority.HIGH.value,
                "severity": CaseSeverity.CRITICAL.value,
                "dept_code": "WATER",
                "cat_code": "WATER_CONTAM",
                "team_name": "Water Emergency Response Unit",
                "assigned_to": op,
                "created_ago_hours": 10,
            },
            # Case 3: Critical Escalated Live Sparking Cable
            {
                "case_number": "MC-2026-1003",
                "title": "Exposed sparking electrical cable dangling over sidewalk",
                "description": "Damaged overhead transformer cable sparking during rain showers. Extreme pedestrian hazard.",
                "ward": "Ward 12 - North",
                "landmark": "Bus Stop #14",
                "address": "Station Road Junction",
                "status": CaseStatus.ESCALATED.value,
                "priority": CasePriority.CRITICAL.value,
                "severity": CaseSeverity.CRITICAL.value,
                "dept_code": "ELECTRICAL",
                "cat_code": "SPARKING_WIRE",
                "team_name": None,
                "assigned_to": op,
                "created_ago_hours": 18,
                "is_escalated": True,
            },
            # Case 4: Resolution Proposed Garbage Overflow
            {
                "case_number": "MC-2026-1004",
                "title": "Overflowing municipal waste dump spreading onto road",
                "description": "Secondary waste bin overflowing, attracting stray animals and blocking half the carriage width.",
                "ward": "Ward 12 - North",
                "landmark": "Opposite Shivaji Market",
                "address": "Market Road, Ward 12",
                "status": CaseStatus.RESOLUTION_PROPOSED.value,
                "priority": CasePriority.MEDIUM.value,
                "severity": CaseSeverity.MODERATE.value,
                "dept_code": "SANITATION",
                "cat_code": "GARBAGE_OVERFLOW",
                "team_name": "Rapid Sanitation Crew",
                "assigned_to": op,
                "created_ago_hours": 24,
                "resolution_notes": "Heavy compactor cleared 3.5 tons waste. Bin power-washed and disinfected with bleaching powder.",
            },
            # Case 5: Confirmed & Closed Streetlight Repair
            {
                "case_number": "MC-2026-1005",
                "title": "Street light pole dark for two consecutive nights",
                "description": "Lamp fixture blown on inner residential street leaving intersection completely dark.",
                "ward": "Ward 12 - North",
                "landmark": "Near Children Park",
                "address": "Green Avenue, Cross #2",
                "status": CaseStatus.CONFIRMED.value,
                "priority": CasePriority.LOW.value,
                "severity": CaseSeverity.MINOR.value,
                "dept_code": "ELECTRICAL",
                "cat_code": "STREET_LIGHT",
                "team_name": None,
                "assigned_to": op,
                "created_ago_hours": 48,
                "resolved_ago_hours": 12,
                "resolution_notes": "Replaced faulty 120W LED fixture and updated junction fuse.",
                "citizen_feedback": "Fast and excellent service. Street is brightly lit now!",
            },
        ]

        for item in cases_to_seed:
            existing_case = db.query(Case).filter(Case.case_number == item["case_number"]).first()
            c_time = now - timedelta(hours=item["created_ago_hours"])

            dept_id = departments[item["dept_code"]].id if item.get("dept_code") else None
            cat_id = categories[item["cat_code"]].id if item.get("cat_code") else None
            team_id = teams[item["team_name"]].id if item.get("team_name") and item["team_name"] in teams else None
            assigned_id = item["assigned_to"].id if item.get("assigned_to") else None

            if not existing_case:
                case = Case(
                    case_number=item["case_number"],
                    title=item["title"],
                    description=item["description"],
                    citizen_id=cit.id,
                    department_id=dept_id,
                    category_id=cat_id,
                    team_id=team_id,
                    assigned_to_id=assigned_id,
                    ward=item["ward"],
                    landmark=item.get("landmark"),
                    address=item.get("address"),
                    status=item["status"],
                    priority=item["priority"],
                    severity=item["severity"],
                    is_escalated=item.get("is_escalated", False),
                    resolution_notes=item.get("resolution_notes"),
                    rejection_reason=item.get("rejection_reason"),
                    created_at=c_time,
                    updated_at=c_time + timedelta(hours=1),
                    closed_at=now - timedelta(hours=item["resolved_ago_hours"]) if "resolved_ago_hours" in item else None,
                )
                db.add(case)
                db.commit()
                db.refresh(case)
            else:
                case = existing_case

            # -----------------------------------------------------------------
            # Attach AI Insights & Triage
            # -----------------------------------------------------------------
            try:
                ai_service.run_case_analysis(db, case_id=case.id, user=op)
            except Exception:
                pass

            # -----------------------------------------------------------------
            # Setup Dynamic SLA
            # -----------------------------------------------------------------
            cat_sla_hours = categories[item["cat_code"]].sla_hours if item.get("cat_code") else 24
            resp_h, res_h = calculate_sla_targets(cat_sla_hours, item["priority"])

            existing_sla = db.query(CaseSLA).filter(CaseSLA.case_id == case.id).first()
            if not existing_sla:
                sla = CaseSLA(
                    case_id=case.id,
                    response_target_hours=resp_h,
                    resolution_target_hours=res_h,
                    response_due_at=c_time + timedelta(hours=resp_h),
                    resolution_due_at=c_time + timedelta(hours=res_h),
                    first_responded_at=c_time + timedelta(minutes=45),
                    resolved_at=case.closed_at or (c_time + timedelta(hours=20) if case.status in [CaseStatus.RESOLUTION_PROPOSED.value, CaseStatus.CONFIRMED.value] else None),
                    response_status=SLAStatus.MET.value,
                    resolution_status=SLAStatus.BREACHED.value if item.get("is_escalated") else (SLAStatus.MET.value if case.closed_at else SLAStatus.WITHIN_TARGET.value),
                    is_breached=bool(item.get("is_escalated")),
                    created_at=c_time,
                )
                db.add(sla)
                db.commit()

            # -----------------------------------------------------------------
            # Add Case Activities (Messages, Tasks, Investigations, Escalation)
            # -----------------------------------------------------------------
            if case.case_number == "MC-2026-1001":
                # Investigation & Tasks
                if not db.query(CaseInvestigation).filter(CaseInvestigation.case_id == case.id).first():
                    db.add(CaseInvestigation(
                        case_id=case.id,
                        investigator_id=op.id,
                        observations="Asphalt surface crumbled creating 15cm deep bowl.",
                        findings="Sub-base weakened by monsoon water drainage accumulation.",
                        actions_taken="Placed reflective barricades and warning cones.",
                        follow_up_requirements="Require 2 tons hot-mix asphalt delivery.",
                        created_at=c_time + timedelta(hours=1),
                    ))
                if not db.query(CaseTask).filter(CaseTask.case_id == case.id).first():
                    db.add(CaseTask(
                        case_id=case.id,
                        title="Dispatch road repair squad with roller",
                        assigned_to_id=op.id,
                        created_by_id=lead.id,
                        status=TaskStatus.IN_PROGRESS.value,
                        created_at=c_time + timedelta(hours=2),
                    ))
                db.commit()

            elif case.case_number == "MC-2026-1002":
                # Chat communication
                if not db.query(CaseMessage).filter(CaseMessage.case_id == case.id).first():
                    db.add(CaseMessage(
                        case_id=case.id,
                        sender_id=op.id,
                        is_from_citizen=False,
                        message="Hello Rahul, could you confirm if the water pressure has dropped alongside the muddy discoloration?",
                        message_type="query",
                        created_at=c_time + timedelta(hours=2),
                    ))
                    db.add(CaseMessage(
                        case_id=case.id,
                        sender_id=cit.id,
                        is_from_citizen=True,
                        message="Yes, pressure is very weak on the top floor and sediment is settling at the bottom of buckets.",
                        message_type="query",
                        created_at=c_time + timedelta(hours=3),
                    ))
                db.commit()

            elif case.case_number == "MC-2026-1003":
                # Escalation record
                if not db.query(CaseEscalation).filter(CaseEscalation.case_id == case.id).first():
                    db.add(CaseEscalation(
                        case_id=case.id,
                        escalated_by_id=op.id,
                        escalated_to_id=lead.id,
                        trigger_type="safety_critical",
                        reason="High voltage cable exposed at bus stop height. Urgent high-priority feeder shutdown required.",
                        status=EscalationStatus.ACKNOWLEDGED.value,
                        created_at=c_time + timedelta(hours=4),
                    ))
                db.commit()

            # -----------------------------------------------------------------
            # Immutable Audit Trail Event
            # -----------------------------------------------------------------
            if not db.query(AuditLog).filter(AuditLog.resource_id == str(case.id), AuditLog.action == "CASE_CREATED").first():
                audit_service.log_event(
                    db=db,
                    action="CASE_CREATED",
                    resource_type="case",
                    resource_id=str(case.id),
                    actor_id=cit.id,
                    details=f"Citizen Rahul Deshmukh registered civic grievance #{case.case_number}",
                    new_values={"case_number": case.case_number, "status": case.status, "priority": case.priority},
                )

        # ---------------------------------------------------------------------
        # 6. Summary Output
        # ---------------------------------------------------------------------
        print("[6/6] Demo Seeding Completed Successfully!")
        print("=" * 70)
        print("READY-TO-USE DEMO LOGIN CREDENTIALS:")
        print("=" * 70)
        for u in user_configs:
            print(f"Role: {u['role'].upper():<15} | Email: {u['email']:<28} | Pwd: Password123")
        print("=" * 70)
        print("Cases Seeded: 5 | Departments: 5 | Categories: 10 | Field Squads: 3")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise e
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    seed_demo_database()
