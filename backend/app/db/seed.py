import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal
from app.core.logging import logger
from app.models.case import Case, CaseStatus, CasePriority, CaseSeverity
from app.models.user import UserRole
from app.schemas.case import CaseCreate
from app.schemas.organization import DepartmentCreate, TeamCreate, CategoryCreate
from app.schemas.user import UserCreate
from app.services.case_service import case_service
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
    """Seed departments, categories, teams, safe demo accounts, and sample cases."""
    logger.info("Starting safe demo database seeding (Departments, Categories, Users, Cases)...")
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
        cat_map = {}
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
                cat_map[cat_data["code"]] = created
                logger.info(f"Created category: {created.name} (SLA: {created.sla_hours}h)")
            else:
                cat_map[cat_data["code"]] = existing

        # 3. Seed Users
        user_map = {}
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
                user_map[user_data["role"].value] = created_user
                logger.info(f"Created demo user: {user_data['email']} ({user_data['role'].value})")
            else:
                user_map[user_data["role"].value] = existing

        # 4. Seed Operational Team
        team_id = None
        if "ROADS" in dept_map:
            roads_dept = dept_map["ROADS"]
            team_lead = user_map.get(UserRole.TEAM_LEAD.value)
            operator = user_map.get(UserRole.OPERATOR.value)

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
                team_id = team.id
                if operator:
                    operator.team_id = team.id
                    db.add(operator)
                    db.commit()
                logger.info(f"Created operational team: {team.name}")
            else:
                team_id = existing_teams[0].id

        # 5. Seed Sample Cases
        citizen = user_map.get(UserRole.REQUESTER.value)
        operator = user_map.get(UserRole.OPERATOR.value)

        existing_cases = db.query(Case).count()
        if existing_cases == 0 and citizen:
            # Case 1: Assigned Pothole Complaint
            pothole_cat = cat_map.get("POTHOLES")
            case1 = case_service.create_case(
                db,
                case_in=CaseCreate(
                    title="Deep Pothole near Main Market Corner",
                    description="Severe 2-foot pothole causing heavy traffic slowdown and two-wheeler accidents near vegetable market gate.",
                    category_id=pothole_cat.id if pothole_cat else None,
                    department_id=dept_map["ROADS"].id if "ROADS" in dept_map else None,
                    ward="Ward 12 - Shivaji Nagar",
                    landmark="Near Main Vegetable Market Gate",
                    priority=CasePriority.HIGH,
                ),
                citizen_id=citizen.id,
            )
            if operator:
                case_service.update_assignment(
                    db,
                    case_obj=case1,
                    actor=operator,
                    assigned_to_id=operator.id,
                    team_id=team_id,
                    reason="Assigned to Ward 12 rapid response unit.",
                )

                # Seed Activities for Case 1 (Pothole)
                # 1. Citizen message
                db.add(CaseMessage(
                    case_id=case1.id,
                    sender_id=citizen.id,
                    message="Please note that school buses pass through this junction every morning at 7:30 AM.",
                    message_type="query",
                    is_from_citizen=True,
                ))
                # 2. Staff response
                db.add(CaseMessage(
                    case_id=case1.id,
                    sender_id=operator.id,
                    message="Thank you for the update. Our inspection team has been deployed with cold asphalt mix.",
                    message_type="staff_update",
                    is_from_citizen=False,
                ))
                # 3. Internal Notes (Private to Staff)
                db.add(InternalNote(
                    case_id=case1.id,
                    author_id=operator.id,
                    note="Dispatched road roller #3 and 2 cubic meters of bitumen gravel from Central Depot.",
                    note_type="investigation_discussion",
                ))
                # 4. Tasks
                db.add(CaseTask(
                    case_id=case1.id,
                    title="Site inspection & barricading",
                    description="Place traffic warning cones and assess depth.",
                    status="completed",
                    assigned_to_id=operator.id,
                    created_by_id=operator.id,
                    order=1,
                ))
                db.add(CaseTask(
                    case_id=case1.id,
                    title="Asphalt patching & compaction",
                    description="Fill pothole with hot mix bitumen and compact level with road surface.",
                    status="in_progress",
                    assigned_to_id=operator.id,
                    created_by_id=operator.id,
                    order=2,
                ))
                # 5. Investigation
                db.add(CaseInvestigation(
                    case_id=case1.id,
                    investigator_id=operator.id,
                    observations="Sub-base eroded due to recent heavy monsoon rainwater runoff from storm drain.",
                    actions_taken="Cleared loose gravel, applied tack coat, placed warning signage.",
                    findings="Drainage culvert blockage caused localized road foundation subsidence.",
                    evidence_notes="Photos taken of damaged road base and culvert inlet.",
                    follow_up_requirements="Stormwater department needs to clear culvert to prevent recurrence.",
                ))

                # 6. Seed Case Attachment (Evidence)
                db.add(CaseAttachment(
                    case_id=case1.id,
                    uploaded_by_id=citizen.id,
                    original_filename="pothole_site_photo.jpg",
                    stored_filename="demo_pothole.jpg",
                    file_path=f"case_{case1.id}/demo_pothole.jpg",
                    file_size=245760,
                    content_type="image/jpeg",
                    description="Photo of damaged road surface taken by citizen at intake.",
                    is_public_to_citizen=True,
                ))
                # 7. Seed AI Analysis
                db.add(AIAnalysis(
                    case_id=case1.id,
                    suggested_category_id=pothole_cat.id if pothole_cat else None,
                    suggested_priority="high",
                    suggested_severity="major",
                    confidence_score=0.91,
                    summary="Severe road pothole reported near vegetable market with school bus impact. Immediate asphalt patching recommended.",
                    key_details=json.dumps(["School bus route transit impacted.", "Active vehicular congestion."]),
                    missing_information=json.dumps(["Exact distance from market gate."]),
                    recommended_action="Deploy road maintenance unit with hot/cold asphalt mix and compacting roller.",
                    suggested_team_id=team_id,
                    risk_insight="HIGH PRIORITY: Location impact suggests compounding traffic disruption if delayed.",
                    duplicate_cases=json.dumps([]),
                ))
                db.commit()

            # Case 2: Reported Garbage Dump
            garbage_cat = cat_map.get("GARBAGE_OVERFLOW")
            case2 = case_service.create_case(
                db,
                case_in=CaseCreate(
                    title="Community Bin Overflowing on Gandhi Road",
                    description="Waste container is full and overflowing onto pedestrian sidewalk for past 3 days. Foul smell spreading.",
                    category_id=garbage_cat.id if garbage_cat else None,
                    department_id=dept_map["WASTE"].id if "WASTE" in dept_map else None,
                    ward="Ward 12 - Shivaji Nagar",
                    landmark="Opposite Gandhi Library",
                    priority=CasePriority.MEDIUM,
                ),
                citizen_id=citizen.id,
            )
            # AI Analysis for Case 2
            db.add(AIAnalysis(
                case_id=case2.id,
                suggested_category_id=garbage_cat.id if garbage_cat else None,
                suggested_priority="medium",
                suggested_severity="moderate",
                confidence_score=0.88,
                summary="Solid waste overflow on pedestrian path. Foul odor spreading near Gandhi Library.",
                key_details=json.dumps(["Public hygiene / vector-borne disease risk."]),
                missing_information=json.dumps(["Is bin physically damaged or only full?"]),
                recommended_action="Dispatch municipal refuse collection compactor vehicle and sanitize container area.",
                suggested_team_id=None,
                risk_insight=None,
                duplicate_cases=json.dumps([]),
            ))
            db.commit()

            # Case 3: Resolution Proposed Streetlight
            light_cat = cat_map.get("STREETLIGHT_OUT")
            case3 = case_service.create_case(
                db,
                case_in=CaseCreate(
                    title="Streetlight Pole #44 Dark on 5th Cross Road",
                    description="Lamp fixture not turning on after sunset creating complete dark spot on residential corner.",
                    category_id=light_cat.id if light_cat else None,
                    department_id=dept_map["ELECTRICAL"].id if "ELECTRICAL" in dept_map else None,
                    ward="Ward 12 - Shivaji Nagar",
                    landmark="5th Cross Road Junction",
                    priority=CasePriority.MEDIUM,
                ),
                citizen_id=citizen.id,
            )
            if operator:
                case_service.update_assignment(db, case_obj=case3, actor=operator, assigned_to_id=operator.id)
                case_service.update_case_status(db, case_obj=case3, new_status=CaseStatus.INVESTIGATED, actor=operator)
                case_service.update_case_status(
                    db,
                    case_obj=case3,
                    new_status=CaseStatus.RESOLUTION_PROPOSED,
                    actor=operator,
                    resolution_notes="Replaced 45W LED driver and tightened cable terminal. Light fixture tested and operational.",
                )
                db.add(AIAnalysis(
                    case_id=case3.id,
                    suggested_category_id=light_cat.id if light_cat else None,
                    suggested_priority="medium",
                    suggested_severity="moderate",
                    confidence_score=0.92,
                    summary="Residential dark spot resolved. LED driver replaced by electrical squad.",
                    key_details=json.dumps(["Nighttime pedestrian safety hazard."]),
                    missing_information=json.dumps([]),
                    recommended_action="Confirm illumination levels with citizen.",
                    suggested_team_id=None,
                    risk_insight=None,
                    duplicate_cases=json.dumps([]),
                ))
                db.commit()

            logger.info("Sample demo cases seeded across reported, assigned, and resolution_proposed states.")

        # 6. Ensure SLA and sample Escalation for existing cases
        all_cases = db.query(Case).all()
        from app.services.sla_service import initialize_or_update_case_sla
        from app.models.escalation import CaseEscalation, EscalationStatus, EscalationTrigger
        for c in all_cases:
            initialize_or_update_case_sla(db, c)

        # Seed sample escalation on Case 1 if none exists
        if all_cases and not db.query(CaseEscalation).first():
            c1 = all_cases[0]
            c1.is_escalated = True
            c1.status = CaseStatus.ESCALATED.value
            db.add(CaseEscalation(
                case_id=c1.id,
                escalated_by_id=user_map.get(UserRole.OPERATOR.value).id if user_map.get(UserRole.OPERATOR.value) else None,
                trigger_type=EscalationTrigger.OPERATOR_REQUEST.value,
                reason="High vehicular congestion and school bus safety risk; requesting immediate asphalt roller dispatch.",
                status=EscalationStatus.ACTIVE.value,
            ))
            db.commit()
            logger.info(f"Seeded sample escalation on Case {c1.case_number}")

        logger.info("Database seeding completed successfully.")

    except Exception as e:
        logger.error(f"Error during seeding: {str(e)}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
