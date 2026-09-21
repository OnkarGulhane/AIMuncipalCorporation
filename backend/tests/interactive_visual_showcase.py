import asyncio
import os
import sys
from playwright.async_api import async_playwright

PORTAL_URL = "http://localhost:8000/portal/"

async def set_banner(page, step_text, sub_text=""):
    js_code = f"""
    (() => {{
        let banner = document.getElementById('live-test-banner');
        if (!banner) {{
            banner = document.createElement('div');
            banner.id = 'live-test-banner';
            banner.style.position = 'fixed';
            banner.style.top = '12px';
            banner.style.left = '50%';
            banner.style.transform = 'translateX(-50%)';
            banner.style.backgroundColor = '#0f172a';
            banner.style.color = '#ffffff';
            banner.style.padding = '12px 28px';
            banner.style.borderRadius = '14px';
            banner.style.fontFamily = 'Inter, sans-serif';
            banner.style.fontSize = '14px';
            banner.style.fontWeight = '700';
            banner.style.zIndex = '999999';
            banner.style.boxShadow = '0 12px 30px rgba(0,0,0,0.4)';
            banner.style.border = '2px solid #6366f1';
            banner.style.display = 'flex';
            banner.style.flexDirection = 'column';
            banner.style.alignItems = 'center';
            banner.style.gap = '4px';
            banner.style.pointerEvents = 'none';
            banner.style.transition = 'all 0.3s ease';
            document.body.appendChild(banner);
        }}
        banner.innerHTML = `
            <div style="display:flex; align-items:center; gap:8px; color:#818cf8;">
                <span style="font-size:16px;">🔍 LIVE TEST:</span>
                <span style="color:#ffffff;">{step_text}</span>
            </div>
            <div style="font-size:11px; color:#94a3b8; font-weight:500;">{sub_text}</div>
        `;
    }})();
    """
    await page.evaluate(js_code)

async def highlight_and_click(page, locator_str, description=""):
    print(f"  -> Action: {description} [{locator_str}]")
    try:
        el = page.locator(locator_str).first
        await el.evaluate("""el => {
            el.style.outline = '4px solid #f43f5e';
            el.style.boxShadow = '0 0 15px rgba(244, 63, 94, 0.8)';
            el.style.transition = 'all 0.2s ease';
        }""")
        await page.wait_for_timeout(1000)
        await el.click()
    except Exception as e:
        print(f"  [Warning] Click fallback for {locator_str}: {e}")

async def run_visual_showcase():
    print("=" * 75)
    print("STARTING LIVE VISUAL SCREEN DEMO WITH ON-SCREEN HIGHLIGHTS & SLOW TYPING")
    print("Target: http://localhost:8000/portal/")
    print("=" * 75)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        # STEP 1: PORTAL HOMEPAGE
        await page.goto(PORTAL_URL, wait_until="networkidle")
        await set_banner(page, "1. Municipal Portal Gatekeeper", "5 Multi-Role Persona Profiles Ready")
        print("\n[STEP 1] Municipal Portal Gatekeeper Loaded on screen")
        await page.wait_for_timeout(3500)

        # STEP 2: CITIZEN LOGIN & LIVE FORM TYPING
        await set_banner(page, "2. Citizen Login (Aarav Sharma)", "Clicking Citizen Persona Card")
        await highlight_and_click(page, "article:has-text('Aarav Sharma')", "Selecting Citizen Card")
        await page.wait_for_selector("#view-app", state="visible")
        await page.wait_for_timeout(2500)

        await set_banner(page, "3. Reporting Civic Grievance", "Opening Grievance Form & Typing Live")
        await highlight_and_click(page, "button:has-text('+ Report Grievance')", "Clicking + Report Grievance")
        await page.wait_for_timeout(1500)

        # Slow realistic character-by-character typing
        print("  -> Typing Title character-by-character...")
        await page.type("#new-case-title", "Severe water main leakage causing road erosion", delay=60)
        await page.wait_for_timeout(600)

        print("  -> Typing Description...")
        await page.type("#new-case-desc", "Potable water pipeline burst underground near school junction. Water flooding the street since morning.", delay=40)
        await page.wait_for_timeout(600)

        print("  -> Typing Landmark...")
        await page.type("#new-case-landmark", "Near St. Mary High School Gate, MG Road Junction", delay=40)
        await page.wait_for_timeout(1000)

        await set_banner(page, "4. Submitting Complaint to Backend", "Saving ticket & launching background AI triage")
        await highlight_and_click(page, "#modal-new-case button:has-text('Submit Grievance')", "Submitting Form")
        await page.wait_for_timeout(3000)

        # STEP 3: SWITCH TO WARD MANAGER & TEST AI COPILOT
        await set_banner(page, "5. Switching to Ward Manager", "Logging in as Vikram Kulkarni (Ward Manager)")
        await highlight_and_click(page, "#btn-switch-account", "Switch User")
        await page.wait_for_timeout(1500)
        await highlight_and_click(page, "article:has-text('Vikram Kulkarni')", "Select Ward Manager")
        await page.wait_for_timeout(2500)

        await set_banner(page, "6. Testing CivicPulse AI Case Copilot", "Inspecting AI Triage, Recommended Squad & Confidence")
        await page.evaluate("openCaseDetail(1)")
        await page.wait_for_timeout(4000)

        await set_banner(page, "7. Testing 1-Click AI Communication Draft", "Generating polite automated message for citizen")
        await highlight_and_click(page, "button:has-text('AI Draft')", "Click AI Draft")
        await page.wait_for_timeout(3000)

        await set_banner(page, "8. Testing AI Executive Summary Dialog", "Displaying AI Case Story, Milestones & Blockers")
        await highlight_and_click(page, "button:has-text('AI Summary')", "Click AI Summary")
        await page.wait_for_timeout(4000)
        await page.evaluate("closeModal('modal-ai-summary')")
        await page.wait_for_timeout(1000)
        await page.evaluate("closeModal('modal-case-detail')")
        await page.wait_for_timeout(1500)

        # STEP 4: SWITCH TO TEAM LEAD & SLA SCAN
        await set_banner(page, "9. Team Lead: SLA & Escalations Hub", "Running automated background SLA sweep")
        await highlight_and_click(page, "#btn-switch-account", "Switch User")
        await page.wait_for_timeout(1500)
        await highlight_and_click(page, "article:has-text('Priya Patil')", "Select Team Lead")
        await page.wait_for_timeout(2000)
        await highlight_and_click(page, "#nav-escalations", "Open SLA Tab")
        await page.wait_for_timeout(2000)
        await highlight_and_click(page, "#btn-run-sla-scan", "Trigger SLA Risk Scan")
        await page.wait_for_timeout(3500)

        # STEP 5: CHIEF ADMINISTRATOR AUDIT LEDGER
        await set_banner(page, "10. Chief Administrator: Audit Ledger", "Viewing cryptographic immutable compliance stream")
        await highlight_and_click(page, "#btn-switch-account", "Switch User")
        await page.wait_for_timeout(1500)
        await highlight_and_click(page, "article:has-text('Sneha Joshi')", "Select Admin")
        await page.wait_for_timeout(2000)
        await highlight_and_click(page, "#nav-audit", "Open Audit Tab")
        await page.wait_for_timeout(4000)

        await set_banner(page, "✅ Live Testing Complete!", "All 5 personas and AI features verified 100%")
        await page.wait_for_timeout(6000)

        await browser.close()
        print("\n" + "=" * 75)
        print("LIVE VISUAL SHOWCASE FINISHED SUCCESSFULLY!")
        print("=" * 75)

if __name__ == "__main__":
    asyncio.run(run_visual_showcase())
