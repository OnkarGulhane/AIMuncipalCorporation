import asyncio
import os
import sys
from playwright.async_api import async_playwright

PORTAL_URL = "http://localhost:8000/portal/"

async def inject_visual_cursor(page):
    js_code = """
    (() => {
        if (document.getElementById('virtual-mouse-cursor')) return;
        
        let cursor = document.createElement('div');
        cursor.id = 'virtual-mouse-cursor';
        cursor.style.position = 'fixed';
        cursor.style.width = '24px';
        cursor.style.height = '24px';
        cursor.style.borderRadius = '50%';
        cursor.style.backgroundColor = 'rgba(239, 68, 68, 0.85)';
        cursor.style.border = '3px solid #ffffff';
        cursor.style.boxShadow = '0 0 15px rgba(239, 68, 68, 0.9), 0 4px 10px rgba(0,0,0,0.3)';
        cursor.style.zIndex = '9999999';
        cursor.style.pointerEvents = 'none';
        cursor.style.transition = 'all 0.5s cubic-bezier(0.25, 1, 0.5, 1)';
        cursor.style.transform = 'translate(-50%, -50%)';
        cursor.style.top = '100px';
        cursor.style.left = '100px';
        document.body.appendChild(cursor);

        let tooltip = document.createElement('div');
        tooltip.id = 'cursor-tooltip';
        tooltip.style.position = 'fixed';
        tooltip.style.padding = '6px 12px';
        tooltip.style.backgroundColor = '#1e1b4b';
        tooltip.style.color = '#ffffff';
        tooltip.style.borderRadius = '8px';
        tooltip.style.fontSize = '12px';
        tooltip.style.fontWeight = 'bold';
        tooltip.style.zIndex = '9999999';
        tooltip.style.pointerEvents = 'none';
        tooltip.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
        tooltip.style.border = '1px solid #818cf8';
        tooltip.style.transition = 'all 0.5s cubic-bezier(0.25, 1, 0.5, 1)';
        tooltip.style.transform = 'translate(15px, 15px)';
        tooltip.innerText = 'AI Virtual Tester';
        document.body.appendChild(tooltip);

        window.moveVisualCursor = (x, y, label) => {
            cursor.style.left = x + 'px';
            cursor.style.top = y + 'px';
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
            if (label) tooltip.innerText = label;
        };

        window.pulseVisualCursor = () => {
            cursor.style.transform = 'translate(-50%, -50%) scale(1.6)';
            setTimeout(() => {
                cursor.style.transform = 'translate(-50%, -50%) scale(1)';
            }, 300);
        };
    })();
    """
    await page.evaluate(js_code)

async def set_banner(page, title, subtitle):
    js_code = f"""
    (() => {{
        let banner = document.getElementById('live-test-banner');
        if (!banner) {{
            banner = document.createElement('div');
            banner.id = 'live-test-banner';
            banner.style.position = 'fixed';
            banner.style.top = '14px';
            banner.style.left = '50%';
            banner.style.transform = 'translateX(-50%)';
            banner.style.backgroundColor = '#0f172a';
            banner.style.color = '#ffffff';
            banner.style.padding = '14px 32px';
            banner.style.borderRadius = '16px';
            banner.style.fontFamily = 'Inter, sans-serif';
            banner.style.fontSize = '15px';
            banner.style.fontWeight = '700';
            banner.style.zIndex = '9999998';
            banner.style.boxShadow = '0 12px 35px rgba(0,0,0,0.5)';
            banner.style.border = '2px solid #6366f1';
            banner.style.display = 'flex';
            banner.style.flexDirection = 'column';
            banner.style.alignItems = 'center';
            banner.style.gap = '4px';
            banner.style.pointerEvents = 'none';
            document.body.appendChild(banner);
        }}
        banner.innerHTML = `
            <div style="display:flex; align-items:center; gap:8px; color:#818cf8;">
                <span style="font-size:18px;">🎯 LIVE AUTOMATED DEMO:</span>
                <span style="color:#ffffff;">{title}</span>
            </div>
            <div style="font-size:12px; color:#cbd5e1; font-weight:500;">{subtitle}</div>
        `;
    }})();
    """
    await page.evaluate(js_code)

async def smooth_move_and_click(page, selector, label):
    try:
        el = page.locator(selector).first
        box = await el.bounding_box()
        if box:
            center_x = box['x'] + box['width'] / 2
            center_y = box['y'] + box['height'] / 2
            await page.evaluate(f"window.moveVisualCursor({center_x}, {center_y}, '{label}')")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.pulseVisualCursor()")
            await page.wait_for_timeout(400)
            await el.click()
        else:
            await el.click()
    except Exception as e:
        print(f"Fallback click for {selector}: {e}")

async def run_persistent_demo():
    print("=" * 70)
    print("LAUNCHING VISIBLE CHROME BROWSER WITH LIVE RED CURSOR OVERLAY")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--window-position=0,0"]
        )
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        # Step 1: Open Portal
        await page.goto(PORTAL_URL, wait_until="networkidle")
        await inject_visual_cursor(page)
        await set_banner(page, "1. Municipal Portal Gatekeeper", "Observe the 5 role cards below")
        await page.wait_for_timeout(3000)

        # Step 2: Citizen Login
        await set_banner(page, "2. Citizen Persona Selected", "Moving cursor to Aarav Sharma card")
        await smooth_move_and_click(page, "article:has-text('Aarav Sharma')", "Clicking Citizen Card")
        await page.wait_for_selector("#view-app", state="visible")
        await inject_visual_cursor(page)
        await page.wait_for_timeout(2000)

        # Step 3: File Grievance Live
        await set_banner(page, "3. Reporting Civic Grievance", "Clicking '+ Report Grievance'")
        await smooth_move_and_click(page, "button:has-text('+ Report Grievance')", "Open Form")
        await page.wait_for_timeout(1500)

        await set_banner(page, "4. Live Form Typing", "Entering title, description and landmark")
        await smooth_move_and_click(page, "#new-case-title", "Typing Title")
        await page.type("#new-case-title", "Dangerous open trench on Station Road", delay=70)
        await page.wait_for_timeout(600)

        await smooth_move_and_click(page, "#new-case-desc", "Typing Description")
        await page.type("#new-case-desc", "Deep excavation left open without warning barricades or safety cones near metro pillar 42.", delay=50)
        await page.wait_for_timeout(600)

        await smooth_move_and_click(page, "#new-case-landmark", "Typing Landmark")
        await page.type("#new-case-landmark", "Metro Pillar 42, Station Road", delay=50)
        await page.wait_for_timeout(1000)

        await set_banner(page, "5. Submitting Grievance", "Sending ticket to FastAPI backend")
        await smooth_move_and_click(page, "#modal-new-case button:has-text('Submit Grievance')", "Submit Form")
        await page.wait_for_timeout(3000)

        # Step 4: Switch to Ward Manager
        await set_banner(page, "6. Switch to Ward Manager", "Clicking Switch Account button in topbar")
        await smooth_move_and_click(page, "#btn-switch-account", "Switch Account")
        await page.wait_for_timeout(1500)
        await inject_visual_cursor(page)

        await set_banner(page, "7. Manager Persona Selected", "Logging in as Vikram Kulkarni (Ward Manager)")
        await smooth_move_and_click(page, "article:has-text('Vikram Kulkarni')", "Click Ward Manager")
        await page.wait_for_timeout(2500)
        await inject_visual_cursor(page)

        # Step 5: Test AI Copilot & AI Draft
        await set_banner(page, "8. CivicPulse AI Copilot", "Opening complaint to view AI Triage & Recommendations")
        await page.evaluate("openCaseDetail(1)")
        await page.wait_for_timeout(4000)
        await inject_visual_cursor(page)

        await set_banner(page, "9. 1-Click AI Communication Draft", "Generating automatic resolution/progress update draft")
        await smooth_move_and_click(page, "button:has-text('AI Draft')", "Click AI Draft")
        await page.wait_for_timeout(3500)

        await set_banner(page, "10. AI Journey Summary Dialog", "Explaining case story and milestones")
        await smooth_move_and_click(page, "button:has-text('AI Summary')", "Click AI Summary")
        await page.wait_for_timeout(4500)
        await page.evaluate("closeModal('modal-ai-summary')")
        await page.wait_for_timeout(1000)
        await page.evaluate("closeModal('modal-case-detail')")
        await page.wait_for_timeout(1500)

        # Step 6: Team Lead SLA Scan
        await set_banner(page, "11. Team Lead: SLA Scan", "Triggering 60s background SLA poller scan")
        await smooth_move_and_click(page, "#btn-switch-account", "Switch Account")
        await page.wait_for_timeout(1500)
        await inject_visual_cursor(page)
        await smooth_move_and_click(page, "article:has-text('Priya Patil')", "Click Team Lead")
        await page.wait_for_timeout(2000)
        await inject_visual_cursor(page)
        await smooth_move_and_click(page, "#nav-escalations", "Open SLA Tab")
        await page.wait_for_timeout(2000)
        await smooth_move_and_click(page, "#btn-run-sla-scan", "Run SLA Scan")
        await page.wait_for_timeout(3500)

        # Step 7: Administrator Audit
        await set_banner(page, "12. Administrator: Audit Ledger", "Viewing cryptographic immutable audit stream")
        await smooth_move_and_click(page, "#btn-switch-account", "Switch Account")
        await page.wait_for_timeout(1500)
        await inject_visual_cursor(page)
        await smooth_move_and_click(page, "article:has-text('Sneha Joshi')", "Click Admin")
        await page.wait_for_timeout(2000)
        await inject_visual_cursor(page)
        await smooth_move_and_click(page, "#nav-audit", "Open Audit Tab")
        await page.wait_for_timeout(3000)

        await set_banner(page, "✨ LIVE DEMO COMPLETED!", "Browser window will stay open for 3 minutes for you to inspect")
        print("\nKeeping browser window open for 180 seconds so you can freely view and test...")
        await page.wait_for_timeout(180000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_persistent_demo())
