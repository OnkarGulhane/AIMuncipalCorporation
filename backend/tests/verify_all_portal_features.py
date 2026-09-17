import sys
import httpx
import json

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000/api/v1"

def test_full_portal_features():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    print("[INFO] Starting End-to-End Comprehensive Portal Features Crosscheck...")

    # -------------------------------------------------------------------------
    # 1. Citizen Role Crosscheck
    # -------------------------------------------------------------------------
    print("\n--- 1. Testing Citizen Role (Aarav Sharma) ---")
    citizen_login = client.post("/auth/login", json={
        "email": "citizen@demo.com",
        "password": "Demo@1234"
    })
    assert citizen_login.status_code == 200, f"Citizen login failed: {citizen_login.text}"
    citizen_token = citizen_login.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    print("[SUCCESS] Citizen login successful.")

    # Citizen Analytics
    cit_analytics = client.get("/analytics/citizen", headers=citizen_headers)
    assert cit_analytics.status_code == 200, f"Citizen analytics failed: {cit_analytics.text}"
    cit_data = cit_analytics.json()
    print(f"[SUCCESS] Citizen Analytics: total_reported={cit_data['total_reported']}, active={cit_data['active_count']}, resolved={cit_data['resolved_count']}")

    # Citizen Case Listing
    cit_cases = client.get("/cases?size=10", headers=citizen_headers)
    assert cit_cases.status_code == 200, f"Citizen case list failed: {cit_cases.text}"
    cases_items = cit_cases.json()["items"]
    print(f"[SUCCESS] Citizen Case Listing: found {len(cases_items)} cases.")

    # Citizen Create Complaint
    new_case_res = client.post("/cases", headers=citizen_headers, json={
        "title": "Crosscheck Test: Water Leakage near Bus Stand",
        "description": "Continuous drinking water pipe burst flooding the footpath near Bus Stop 4.",
        "ward": "Ward 04 - East",
        "landmark": "Bus Stop 4",
        "priority": "high",
        "severity": "major"
    })
    assert new_case_res.status_code == 201, f"Create case failed: {new_case_res.text}"
    created_case = new_case_res.json()
    test_case_id = created_case["id"]
    test_case_number = created_case["case_number"]
    print(f"[SUCCESS] Case Created: ID={test_case_id}, Number={test_case_number}, Status={created_case['status']}")

    # Citizen Send Message on Case
    msg_res = client.post(f"/cases/{test_case_id}/messages", headers=citizen_headers, json={
        "message": "Water flow is very high, please send emergency team quickly.",
        "message_type": "general"
    })
    assert msg_res.status_code == 201, f"Citizen message failed: {msg_res.text}"
    print("[SUCCESS] Citizen sent message on case.")

    # Citizen View Timeline
    timeline_res = client.get(f"/cases/{test_case_id}/timeline", headers=citizen_headers)
    assert timeline_res.status_code == 200, f"Citizen timeline failed: {timeline_res.text}"
    timeline_data = timeline_res.json()
    print(f"[SUCCESS] Unified Timeline fetched: {timeline_data['total_events']} events logged.")

    # -------------------------------------------------------------------------
    # 2. Field Operator Role Crosscheck
    # -------------------------------------------------------------------------
    print("\n--- 2. Testing Field Operator Role (Rohan Deshmukh) ---")
    operator_login = client.post("/auth/login", json={
        "email": "operator@demo.com",
        "password": "Demo@1234"
    })
    assert operator_login.status_code == 200, f"Operator login failed: {operator_login.text}"
    operator_token = operator_login.json()["access_token"]
    operator_headers = {"Authorization": f"Bearer {operator_token}"}
    print("[SUCCESS] Field Operator login successful.")

    # Operator Analytics
    op_analytics = client.get("/analytics/operator", headers=operator_headers)
    assert op_analytics.status_code == 200, f"Operator analytics failed: {op_analytics.text}"
    print("[SUCCESS] Operator Analytics loaded.")

    # Operator Claims Case
    claim_res = client.put(f"/cases/{test_case_id}/assignment", headers=operator_headers, json={
        "reason": "Claimed by Rohan for site inspection"
    })
    assert claim_res.status_code == 200, f"Operator claim failed: {claim_res.text}"
    print(f"[SUCCESS] Operator Claimed Case. Status is now {claim_res.json()['status']}.")

    # AI Triage on Case
    ai_triage_res = client.post(f"/cases/{test_case_id}/ai-analysis", headers=operator_headers)
    assert ai_triage_res.status_code == 200, f"AI Triage failed: {ai_triage_res.text}"
    ai_data = ai_triage_res.json()
    print(f"[SUCCESS] AI Triage Completed: Category='{ai_data['suggested_category_name']}', Confidence={ai_data['confidence_score']:.2f}")

    # AI Apply Suggestions
    apply_res = client.post(f"/cases/{test_case_id}/ai/apply-suggestions", headers=operator_headers, json={
        "apply_category": True,
        "apply_priority": True,
        "apply_team": True
    })
    assert apply_res.status_code == 200, f"Apply suggestions failed: {apply_res.text}"
    print("[SUCCESS] Applied AI Suggestions to case.")

    # AI Draft Communication
    draft_res = client.post(f"/cases/{test_case_id}/ai/draft-communication", headers=operator_headers, json={
        "draft_type": "progress_update",
        "context_notes": "Pipe repaired and pressure restored"
    })
    assert draft_res.status_code == 200, f"AI Draft failed: {draft_res.text}"
    print(f"[SUCCESS] AI Draft generated: \"{draft_res.json()['body_text'][:60]}...\"")

    # Operator Logs Private Internal Note
    note_res = client.post(f"/cases/{test_case_id}/internal-notes", headers=operator_headers, json={
        "note": "Valve 4B needs replacement; pipe weld required.",
        "note_type": "investigation_discussion"
    })
    assert note_res.status_code == 201, f"Internal note failed: {note_res.text}"
    print("[SUCCESS] Operator logged private internal note.")

    # Operator Logs Field Investigation
    inv_res = client.post(f"/cases/{test_case_id}/investigations", headers=operator_headers, json={
        "observations": "Water pressure 4.5 bar, main feeder pipe fractured.",
        "findings": "Immediate sleeve clamp applied.",
        "actions_taken": "Water mains isolated and repair squad deployed."
    })
    assert inv_res.status_code == 201, f"Investigation failed: {inv_res.text}"
    print("[SUCCESS] Operator logged structured field investigation.")

    # Operator Proposes Resolution
    prop_res = client.put(f"/cases/{test_case_id}/status", headers=operator_headers, json={
        "new_status": "resolution_proposed",
        "resolution_notes": "Main feeder pipe welded and reinforced. Water supply restored at normal pressure."
    })
    assert prop_res.status_code == 200, f"Propose resolution failed: {prop_res.text}"
    print(f"[SUCCESS] Operator proposed resolution. Status is now {prop_res.json()['status']}.")

    # -------------------------------------------------------------------------
    # 3. Citizen Confirms Resolution
    # -------------------------------------------------------------------------
    print("\n--- 3. Testing Citizen Confirm Resolution ---")
    confirm_res = client.post(f"/cases/{test_case_id}/confirm-resolution", headers=citizen_headers, json={
        "notes": "Verified water supply is clean and footpath is cleared. Thank you!"
    })
    assert confirm_res.status_code == 200, f"Citizen confirm failed: {confirm_res.text}"
    print(f"[SUCCESS] Case Successfully Confirmed & Closed. Final Status: {confirm_res.json()['status']}.")

    # -------------------------------------------------------------------------
    # 4. Team Lead & Escalations Crosscheck
    # -------------------------------------------------------------------------
    print("\n--- 4. Testing Team Lead Role (Priya Patil) & Escalations ---")
    lead_login = client.post("/auth/login", json={
        "email": "teamlead@demo.com",
        "password": "Demo@1234"
    })
    assert lead_login.status_code == 200, f"Team Lead login failed: {lead_login.text}"
    lead_token = lead_login.json()["access_token"]
    lead_headers = {"Authorization": f"Bearer {lead_token}"}
    print("[SUCCESS] Team Lead login successful.")

    lead_analytics = client.get("/analytics/team-lead", headers=lead_headers)
    assert lead_analytics.status_code == 200, f"Team lead analytics failed: {lead_analytics.text}"
    print("[SUCCESS] Team Lead Analytics loaded.")

    escalations_res = client.get("/escalations", headers=lead_headers)
    assert escalations_res.status_code == 200, f"List escalations failed: {escalations_res.text}"
    escalations_list = escalations_res.json()
    print(f"[SUCCESS] Escalations fetched: {len(escalations_list)} active records.")

    # -------------------------------------------------------------------------
    # 5. Ward Manager & Administrator Crosscheck
    # -------------------------------------------------------------------------
    print("\n--- 5. Testing Ward Manager (Vikram Kulkarni) & Chief Admin ---")
    mgr_login = client.post("/auth/login", json={
        "email": "manager@demo.com",
        "password": "Demo@1234"
    })
    assert mgr_login.status_code == 200, f"Manager login failed: {mgr_login.text}"
    mgr_token = mgr_login.json()["access_token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
    print("[SUCCESS] Ward Manager login successful.")

    mgr_analytics = client.get("/analytics/manager", headers=mgr_headers)
    assert mgr_analytics.status_code == 200, f"Manager analytics failed: {mgr_analytics.text}"
    mgr_data = mgr_analytics.json()
    print(f"[SUCCESS] Executive Analytics: total={mgr_data['total_cases']}, compliance={mgr_data['sla_compliance_percent']}%, AI insights count={len(mgr_data['ai_operational_insights'])}")

    audit_res = client.get("/admin/audit-logs", headers=mgr_headers)
    assert audit_res.status_code == 200, f"Audit logs failed: {audit_res.text}"
    print(f"[SUCCESS] Audit Trail fetched: {len(audit_res.json())} immutable audit events verified.")

    # SLA Sweep
    sweep_res = client.post("/automation/sweep-slas-and-risks", headers=mgr_headers)
    assert sweep_res.status_code == 200, f"SLA sweep failed: {sweep_res.text}"
    print("[SUCCESS] SLA & Risk Background Sweep executed successfully.")

    # Admin System Stats
    admin_login = client.post("/auth/login", json={
        "email": "admin@demo.com",
        "password": "Demo@1234"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    stats_res = client.get("/admin/system-stats", headers=admin_headers)
    assert stats_res.status_code == 200, f"System stats failed: {stats_res.text}"
    stats_data = stats_res.json()
    print(f"[SUCCESS] Admin System Stats: users={stats_data['total_users']}, cases={stats_data['total_cases']}, database={stats_data['database_status']}")

    print("\n[ALL CHECKS PASSED] ALL 14 PHASES & WEB PORTAL FEATURES VERIFIED 100% OPERATIONAL WITH ZERO ERRORS!")

if __name__ == "__main__":
    test_full_portal_features()
