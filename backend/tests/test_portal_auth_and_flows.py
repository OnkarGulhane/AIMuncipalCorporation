import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# -----------------------------------------------------------------------------
# 1. TEST ALL 5 PRE-SEEDED ROLE LOGINS & PROFILES
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("email,password,expected_role,expected_name", [
    ("citizen@demo.com", "Demo@1234", "requester", "Aarav Sharma"),
    ("operator@demo.com", "Demo@1234", "operator", "Rohan Deshmukh"),
    ("teamlead@demo.com", "Demo@1234", "team_lead", "Priya Patil"),
    ("manager@demo.com", "Demo@1234", "manager", "Vikram Kulkarni"),
    ("admin@demo.com", "Demo@1234", "administrator", "Sneha Joshi"),
])
def test_all_5_roles_separate_login(email, password, expected_role, expected_name):
    # Perform standard login
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert data["user"]["role"] == expected_role
    assert expected_name in data["user"]["full_name"]

    # Validate session via /auth/me
    token = data["access_token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == email
    assert me_data["role"] == expected_role


# -----------------------------------------------------------------------------
# 2. TEST NEGATIVE LOGIN PATHS
# -----------------------------------------------------------------------------
def test_login_invalid_credentials():
    # Wrong password
    res = client.post("/api/v1/auth/login", json={
        "email": "citizen@demo.com",
        "password": "WrongPassword@999"
    })
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]

    # Nonexistent email
    res2 = client.post("/api/v1/auth/login", json={
        "email": "nonexistent_user@test.org",
        "password": "Demo@1234"
    })
    assert res2.status_code == 401


# -----------------------------------------------------------------------------
# 3. TEST CITIZEN SELF-REGISTRATION & IMMEDIATE LOGIN
# -----------------------------------------------------------------------------
def test_citizen_self_registration_flow():
    import uuid
    unique_email = f"citizen_{uuid.uuid4().hex[:8]}@testcivic.org"
    
    # 1. Register new citizen
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Test Citizen User",
        "email": unique_email,
        "password": "SecurePassword@123",
        "phone_number": "+919876543210"
    })
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["role"] == "requester"
    assert reg_data["user"]["email"] == unique_email

    # 2. Login with registered credentials
    login_res = client.post("/api/v1/auth/login", json={
        "email": unique_email,
        "password": "SecurePassword@123"
    })
    assert login_res.status_code == 200
    assert login_res.json()["user"]["email"] == unique_email


# -----------------------------------------------------------------------------
# 4. TEST STATIC PORTAL ASSETS AND HTML DELIVERY
# -----------------------------------------------------------------------------
def test_static_portal_endpoints_delivery():
    # Portal HTML
    portal_res = client.get("/portal/", follow_redirects=True)
    assert portal_res.status_code == 200
    html_text = portal_res.text
    assert "auth-overlay" in html_text
    assert "app-header" in html_text
    assert "user-profile-chip" in html_text
    assert "btn-logout" in html_text
    assert "app-main" in html_text
    assert "modal-case-detail" in html_text

    # Static CSS
    css_res = client.get("/portal/styles.css")
    assert css_res.status_code == 200
    assert ".auth-overlay-backdrop" in css_res.text
    assert ".modal-box" in css_res.text

    # Static JS
    js_res = client.get("/portal/app.js")
    assert js_res.status_code == 200
    assert "performLogin" in js_res.text
    assert "performLogout" in js_res.text
    assert "selectDemoRole" in js_res.text
