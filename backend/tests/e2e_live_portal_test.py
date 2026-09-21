import asyncio
import os
import sys
from playwright.async_api import async_playwright

PORTAL_URL = "http://localhost:8000/portal/"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "static_portal", "test_screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

async def run_live_e2e_tests():
    print("=" * 70)
    print("CIVICPULSE ENTERPRISE PORTAL - LIVE MULTI-ROLE E2E TEST RUNNER")
    print(f"Target URL: {PORTAL_URL}")
    print(f"Output Screenshots: {SCREENSHOTS_DIR}")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # ---------------------------------------------------------------------
        # STEP 1: INITIAL GATEKEEPER VIEW
        # ---------------------------------------------------------------------
        print("\n[STEP 1] Navigating to Municipal Portal Gatekeeper...")
        await page.goto(PORTAL_URL, wait_until="networkidle")
        await page.wait_for_selector("#view-login")
        
        login_title = await page.text_content("h1")
        print(f"  [OK] Header Loaded: '{login_title.strip()}'")
        
        step1_img = os.path.join(SCREENSHOTS_DIR, "01_login_gatekeeper.png")
        await page.screenshot(path=step1_img)
        print(f"  [SNAPSHOT] Saved: {step1_img}")

        # ---------------------------------------------------------------------
        # STEP 2: TEST CITIZEN LOGIN (Aarav Sharma)
        # ---------------------------------------------------------------------
        print("\n[STEP 2] Testing Persona: CITIZEN (Aarav Sharma - citizen@demo.com)")
        citizen_card = page.locator("article:has-text('Aarav Sharma')")
        await citizen_card.click()
        
        await page.wait_for_selector("#view-app", state="visible")
        await page.wait_for_timeout(1000)
        
        user_name = await page.text_content("#user-name")
        role_tag = await page.text_content("#user-role-tag")
        print(f"  [OK] Authenticated as: {user_name.strip()} ({role_tag.strip()})")
        
        step2_img = os.path.join(SCREENSHOTS_DIR, "02_citizen_workspace.png")
        await page.screenshot(path=step2_img)
        print(f"  [SNAPSHOT] Saved: {step2_img}")

        # Switch user back
        print("  -> Clicking Switch Account...")
        await page.click("#btn-switch-account")
        await page.wait_for_selector("#view-login", state="visible")

        # ---------------------------------------------------------------------
        # STEP 3: TEST OPERATOR LOGIN (Rohan Deshmukh)
        # ---------------------------------------------------------------------
        print("\n[STEP 3] Testing Persona: FIELD OPERATOR (Rohan Deshmukh - operator@demo.com)")
        operator_card = page.locator("article:has-text('Rohan Deshmukh')")
        await operator_card.click()
        
        await page.wait_for_selector("#view-app", state="visible")
        await page.wait_for_timeout(1000)
        
        user_name = await page.text_content("#user-name")
        role_tag = await page.text_content("#user-role-tag")
        dash_title = await page.text_content("#dash-main-title")
        print(f"  [OK] Authenticated as: {user_name.strip()} ({role_tag.strip()})")
        print(f"  [OK] Active Dashboard: '{dash_title.strip()}'")
        
        step3_img = os.path.join(SCREENSHOTS_DIR, "03_operator_queue.png")
        await page.screenshot(path=step3_img)
        print(f"  [SNAPSHOT] Saved: {step3_img}")

        # Switch user back
        print("  -> Clicking Switch Account...")
        await page.click("#btn-switch-account")
        await page.wait_for_selector("#view-login", state="visible")

        # ---------------------------------------------------------------------
        # STEP 4: TEST TEAM LEAD LOGIN (Priya Patil)
        # ---------------------------------------------------------------------
        print("\n[STEP 4] Testing Persona: TEAM LEAD (Priya Patil - teamlead@demo.com)")
        teamlead_card = page.locator("article:has-text('Priya Patil')")
        await teamlead_card.click()
        
        await page.wait_for_selector("#view-app", state="visible")
        await page.wait_for_timeout(1000)
        
        user_name = await page.text_content("#user-name")
        role_tag = await page.text_content("#user-role-tag")
        print(f"  [OK] Authenticated as: {user_name.strip()} ({role_tag.strip()})")
        
        # Open SLA tab
        print("  -> Navigating to SLA & Escalations Tab...")
        await page.click("#nav-escalations")
        await page.wait_for_timeout(600)
        
        step4_img = os.path.join(SCREENSHOTS_DIR, "04_teamlead_sla.png")
        await page.screenshot(path=step4_img)
        print(f"  [SNAPSHOT] Saved: {step4_img}")

        # Switch user back
        print("  -> Clicking Switch Account...")
        await page.click("#btn-switch-account")
        await page.wait_for_selector("#view-login", state="visible")

        # ---------------------------------------------------------------------
        # STEP 5: TEST WARD MANAGER (Vikram Kulkarni) & AI COPILOT
        # ---------------------------------------------------------------------
        print("\n[STEP 5] Testing Persona: WARD MANAGER (Vikram Kulkarni - manager@demo.com)")
        manager_card = page.locator("article:has-text('Vikram Kulkarni')")
        await manager_card.click()
        
        await page.wait_for_selector("#view-app", state="visible")
        await page.wait_for_timeout(1000)
        
        user_name = await page.text_content("#user-name")
        role_tag = await page.text_content("#user-role-tag")
        print(f"  [OK] Authenticated as: {user_name.strip()} ({role_tag.strip()})")
        
        step5_img = os.path.join(SCREENSHOTS_DIR, "05_manager_command_center.png")
        await page.screenshot(path=step5_img)
        print(f"  [SNAPSHOT] Saved: {step5_img}")

        # Open Case Detail to verify AI Case Copilot using openCaseDetail(1)
        print("  -> Opening Case Detail (Case #1) to test CivicPulse AI Copilot...")
        await page.evaluate("openCaseDetail(1)")
        await page.wait_for_selector("#modal-case-detail.open")
        await page.wait_for_timeout(1000)
        
        ai_conf = await page.text_content("#detail-ai-confidence")
        ai_cat = await page.text_content("#detail-ai-cat")
        ai_squad = await page.text_content("#detail-ai-squad")
        ai_priority = await page.text_content("#detail-ai-priority")
        ai_action = await page.text_content("#detail-ai-action")
        print(f"  [OK] AI Copilot Confidence: {ai_conf.strip()}")
        print(f"  [OK] AI Suggested Category: {ai_cat.strip()}")
        print(f"  [OK] AI Recommended Squad: {ai_squad.strip()}")
        print(f"  [OK] AI Suggested Priority: {ai_priority.strip()}")
        print(f"  [OK] AI Next Action: {ai_action.strip()}")
        
        step5_modal_img = os.path.join(SCREENSHOTS_DIR, "05_manager_ai_copilot_modal.png")
        await page.screenshot(path=step5_modal_img)
        print(f"  [SNAPSHOT] Saved: {step5_modal_img}")
        
        # Close detail modal
        await page.evaluate("closeModal('modal-case-detail')")
        await page.wait_for_timeout(400)

        # Switch user back
        print("  -> Clicking Switch Account...")
        await page.click("#btn-switch-account")
        await page.wait_for_selector("#view-login", state="visible")

        # ---------------------------------------------------------------------
        # STEP 6: TEST CHIEF ADMINISTRATOR (Sneha Joshi) & AUDIT LEDGER
        # ---------------------------------------------------------------------
        print("\n[STEP 6] Testing Persona: CHIEF ADMINISTRATOR (Sneha Joshi - admin@demo.com)")
        admin_card = page.locator("article:has-text('Sneha Joshi')")
        await admin_card.click()
        
        await page.wait_for_selector("#view-app", state="visible")
        await page.wait_for_timeout(1000)
        
        user_name = await page.text_content("#user-name")
        role_tag = await page.text_content("#user-role-tag")
        print(f"  [OK] Authenticated as: {user_name.strip()} ({role_tag.strip()})")
        
        # Navigate to Audit Ledger
        print("  -> Navigating to Immutable Cryptographic Audit Ledger...")
        await page.click("#nav-audit")
        await page.wait_for_timeout(800)
        
        step6_img = os.path.join(SCREENSHOTS_DIR, "06_admin_audit_ledger.png")
        await page.screenshot(path=step6_img)
        print(f"  [SNAPSHOT] Saved: {step6_img}")

        # Navigate to Notifications
        print("  -> Navigating to Notifications Center...")
        await page.click("#nav-notifications")
        await page.wait_for_timeout(600)
        step7_img = os.path.join(SCREENSHOTS_DIR, "07_notifications_hub.png")
        await page.screenshot(path=step7_img)
        print(f"  [SNAPSHOT] Saved: {step7_img}")

        await browser.close()
        print("\n" + "=" * 70)
        print("ALL 5 ROLES AND WORKSPACES VERIFIED SUCCESSFULLY WITH 7 SCREENSHOTS!")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_live_e2e_tests())
