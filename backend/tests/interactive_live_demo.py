import asyncio
import os
import sys
from playwright.async_api import async_playwright

PORTAL_URL = "http://localhost:8000/portal/"

async def run_visible_desktop_demo():
    print("=" * 70)
    print("OPENING REAL VISIBLE CHROME BROWSER ON YOUR SCREEN...")
    print(f"Target URL: {PORTAL_URL}")
    print("=" * 70)

    async with async_playwright() as p:
        # Launch Chromium with headless=False so it opens a real visible window on the user's desktop!
        browser = await p.chromium.launch(headless=False, slow_mo=1200)
        context = await browser.new_context(viewport={"width": 1366, "height": 768})
        page = await context.new_page()

        # STEP 1: OPEN PORTAL
        print("\n[1/6] Opening CivicPulse Portal in visible browser...")
        await page.goto(PORTAL_URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # STEP 2: LOGIN AS CITIZEN & FILE COMPLAINT
        print("\n[2/6] Logging in as Citizen (Aarav Sharma)...")
        await page.click("article:has-text('Aarav Sharma')")
        await page.wait_for_timeout(2000)

        print("  -> Clicking '+ Report Grievance'...")
        await page.click("button:has-text('+ Report Grievance')")
        await page.wait_for_timeout(1500)

        print("  -> Typing grievance details live...")
        await page.fill("#new-case-title", "Severe pothole and water accumulation near Shivaji Nagar Chowk")
        await page.wait_for_timeout(800)
        await page.fill("#new-case-desc", "Heavy rain has caused a 2-foot deep crater obstructing school buses and daily commuter vehicles.")
        await page.wait_for_timeout(800)
        await page.fill("#new-case-landmark", "Opposite City Union Bank, Shivaji Nagar Main Junction")
        await page.wait_for_timeout(1000)

        print("  -> Submitting grievance...")
        await page.click("#modal-new-case button:has-text('Submit Grievance')")
        await page.wait_for_timeout(2500)

        # STEP 3: SWITCH TO WARD MANAGER & TEST AI COPILOT
        print("\n[3/6] Switching to Ward Manager (Vikram Kulkarni)...")
        await page.click("#btn-switch-account")
        await page.wait_for_timeout(1500)
        await page.click("article:has-text('Vikram Kulkarni')")
        await page.wait_for_timeout(2000)

        print("  -> Opening newly created complaint to view AI Copilot...")
        await page.evaluate("openCaseDetail(1)")
        await page.wait_for_timeout(3000)

        print("  -> Testing AI Draft message generation...")
        await page.click("button:has-text('AI Draft')")
        await page.wait_for_timeout(2000)

        print("  -> Viewing AI Case Journey Summary dialog...")
        await page.click("button:has-text('AI Summary')")
        await page.wait_for_timeout(3000)
        await page.evaluate("closeModal('modal-ai-summary')")
        await page.wait_for_timeout(1000)

        await page.evaluate("closeModal('modal-case-detail')")
        await page.wait_for_timeout(1500)

        # STEP 4: SWITCH TO OPERATOR & LOG INVESTIGATION
        print("\n[4/6] Switching to Field Operator (Rohan Deshmukh)...")
        await page.click("#btn-switch-account")
        await page.wait_for_timeout(1500)
        await page.click("article:has-text('Rohan Deshmukh')")
        await page.wait_for_timeout(2000)

        # STEP 5: TEAM LEAD & SLA SCAN
        print("\n[5/6] Switching to Team Lead (Priya Patil) & Running SLA Risk Scan...")
        await page.click("#btn-switch-account")
        await page.wait_for_timeout(1500)
        await page.click("article:has-text('Priya Patil')")
        await page.wait_for_timeout(2000)
        await page.click("#nav-escalations")
        await page.wait_for_timeout(1500)
        await page.click("#btn-run-sla-scan")
        await page.wait_for_timeout(2500)

        # STEP 6: CHIEF ADMINISTRATOR AUDIT LEDGER
        print("\n[6/6] Switching to Administrator (Sneha Joshi) & Reviewing Audit Ledger...")
        await page.click("#btn-switch-account")
        await page.wait_for_timeout(1500)
        await page.click("article:has-text('Sneha Joshi')")
        await page.wait_for_timeout(2000)
        await page.click("#nav-audit")
        await page.wait_for_timeout(3000)

        print("\nDemo completed. Keeping browser visible for 5 seconds...")
        await page.wait_for_timeout(5000)
        await browser.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(run_visible_desktop_demo())
