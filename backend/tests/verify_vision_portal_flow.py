import sys
import io
import json
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def test_full_vision_portal_workflow():
    print("=" * 70)
    print("🚀 TESTING AI CAMERA & VISION ZERO-TYPING FLOW")
    print("=" * 70)

    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # 1. Login as Citizen (Aarav Sharma)
    print("\n1. Logging in as Citizen (Aarav Sharma)...")
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "citizen@demo.com",
        "password": "Demo@1234"
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Citizen login successful. Token acquired.")

    # 2. Test AI Vision Triage with JSON payload (Pothole demo)
    print("\n2. Testing AI Camera Vision Triage (JSON Payload: Pothole)...")
    pothole_payload = {
        "filename": "camera_snap_crater_pothole.jpg",
        "landmark_hint": "Opposite City Bank ATM, MG Road",
        "voice_note": "deep dangerous asphalt pothole causing traffic jam"
    }
    vis_resp = client.post("/api/v1/cases/ai/vision-triage", json=pothole_payload, headers=headers)
    assert vis_resp.status_code == 200, f"Vision triage failed: {vis_resp.text}"
    pothole_data = vis_resp.json()
    print("   ✅ AI Vision Response:")
    print(f"      - Detected Issue: {pothole_data['detected_issue']}")
    print(f"      - Category Name: {pothole_data['category_name']}")
    print(f"      - Confidence Score: {pothole_data['confidence_score'] * 100:.1f}%")
    print(f"      - Auto-Filled Title: {pothole_data['suggested_title']}")
    print(f"      - Auto-Filled Priority: {pothole_data['suggested_priority'].upper()}")
    print(f"      - Visual Tags: {', '.join(pothole_data['visual_tags'])}")

    assert pothole_data["detected_issue"] == "POTHOLES"
    assert pothole_data["confidence_score"] >= 0.90

    # 3. Test AI Vision Triage with Multipart File Upload (Garbage Dump photo)
    print("\n3. Testing AI Camera Vision Triage (Multipart Photo Upload: Garbage)...")
    fake_img = b"\xff\xd8\xff\xe0" + b"\x00" * 200
    files = {
        "file": ("camera_snap_garbage_dump_overflow.jpg", fake_img, "image/jpeg")
    }
    data = {
        "landmark_hint": "Near Shivaji Park Gate 3",
        "voice_note": "overflowing garbage container with litter on the pavement"
    }
    vis_upload_resp = client.post("/api/v1/cases/ai/vision-triage-upload", files=files, data=data, headers=headers)
    assert vis_upload_resp.status_code == 200, f"Vision upload failed: {vis_upload_resp.text}"
    waste_data = vis_upload_resp.json()
    print("   ✅ AI Vision Photo Upload Response:")
    print(f"      - Detected Issue: {waste_data['detected_issue']}")
    print(f"      - Category Name: {waste_data['category_name']}")
    print(f"      - Confidence Score: {waste_data['confidence_score'] * 100:.1f}%")
    print(f"      - Auto-Filled Title: {waste_data['suggested_title']}")
    print(f"      - Auto-Filled Priority: {waste_data['suggested_priority'].upper()}")

    assert waste_data["detected_issue"] == "GARBAGE_OVERFLOW"

    # 4. Create Grievance using the AI Vision Auto-Filled Data (Zero Typing)
    print("\n4. Registering Civic Grievance with Zero-Typing AI Form Data...")
    case_payload = {
        "title": pothole_data["suggested_title"],
        "description": pothole_data["suggested_description"],
        "category_id": pothole_data["category_id"],
        "ward": "Ward 12 - Shivaji Nagar",
        "landmark": pothole_data["landmark_inferred"],
        "priority": pothole_data["suggested_priority"],
        "severity": pothole_data["suggested_severity"]
    }
    case_resp = client.post("/api/v1/cases", json=case_payload, headers=headers)
    assert case_resp.status_code == 201, f"Case creation failed: {case_resp.status_code} {case_resp.text}"
    new_case = case_resp.json()
    print(f"   ✅ Grievance Registered Successfully!")
    print(f"      - Case ID: {new_case['id']}")
    print(f"      - Case Number: {new_case['case_number']}")
    print(f"      - Status: {new_case['status'].upper()}")
    print(f"      - Ward: {new_case['ward']}")
    print(f"      - Priority: {new_case['priority'].upper()}")

    # 5. Verify Case Detail and Unified Timeline
    print(f"\n5. Verifying Case Details & Timeline for {new_case['case_number']}...")
    detail_resp = client.get(f"/api/v1/cases/{new_case['id']}", headers=headers)
    assert detail_resp.status_code == 200
    timeline_resp = client.get(f"/api/v1/cases/{new_case['id']}/timeline", headers=headers)
    assert timeline_resp.status_code == 200
    print(f"   ✅ Case Detail & Unified Timeline retrieved cleanly (Total events: {len(timeline_resp.json())}).")

    print("\n" + "=" * 70)
    print("🎉 ALL AI CAMERA & ZERO-TYPING TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_vision_portal_workflow()
