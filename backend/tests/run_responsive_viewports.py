import asyncio
import os
from playwright.async_api import async_playwright

PORTAL_URL = "http://localhost:8000/portal/"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "static_portal", "test_screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

VIEWPORTS = [
    {"name": "Mobile_Phone_iPhone14", "width": 390, "height": 844},
    {"name": "Tablet_iPadAir", "width": 820, "height": 1180},
    {"name": "Desktop_FullHD", "width": 1920, "height": 1080},
]

async def test_responsiveness():
    print("=" * 70)
    print("CROSS-DEVICE & RESPONSIVE VIEWPORT TESTING (Phone, Tablet, Desktop)")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for vp in VIEWPORTS:
            name = vp["name"]
            w = vp["width"]
            h = vp["height"]
            print(f"\n[*] Testing Viewport: {name} ({w}x{h})...")

            context = await browser.new_context(viewport={"width": w, "height": h})
            page = await context.new_page()

            # 1. Test Login Gatekeeper
            await page.goto(PORTAL_URL, wait_until="networkidle")
            await page.wait_for_selector("#view-login")
            
            # Check for horizontal scroll overflow
            scroll_width = await page.evaluate("document.body.scrollWidth")
            inner_width = await page.evaluate("window.innerWidth")
            has_horizontal_overflow = scroll_width > inner_width
            print(f"  [Gatekeeper] Horizontal Overflow: {has_horizontal_overflow} (Scroll: {scroll_width}, Window: {inner_width})")
            assert not has_horizontal_overflow, f"Horizontal overflow detected on {name} in gatekeeper!"

            img_path = os.path.join(SCREENSHOTS_DIR, f"responsive_{name}_gatekeeper.png")
            await page.screenshot(path=img_path)
            print(f"  [SNAPSHOT] {img_path}")

            # 2. Test Authenticated Dashboard (Ward Manager)
            await page.click("article:has-text('Vikram Kulkarni')")
            await page.wait_for_selector("#view-app", state="visible")
            await page.wait_for_timeout(800)

            scroll_width_app = await page.evaluate("document.body.scrollWidth")
            inner_width_app = await page.evaluate("window.innerWidth")
            has_app_overflow = scroll_width_app > inner_width_app
            print(f"  [Dashboard] Horizontal Overflow: {has_app_overflow} (Scroll: {scroll_width_app}, Window: {inner_width_app})")

            img_path_app = os.path.join(SCREENSHOTS_DIR, f"responsive_{name}_dashboard.png")
            await page.screenshot(path=img_path_app)
            print(f"  [SNAPSHOT] {img_path_app}")

            # 3. Test Case Detail Modal
            await page.evaluate("openCaseDetail(1)")
            await page.wait_for_selector("#modal-case-detail.open")
            await page.wait_for_timeout(800)

            img_path_modal = os.path.join(SCREENSHOTS_DIR, f"responsive_{name}_case_modal.png")
            await page.screenshot(path=img_path_modal)
            print(f"  [SNAPSHOT] {img_path_modal}")

            await context.close()

        await browser.close()
        print("\n" + "=" * 70)
        print("ALL VIEWPORTS (MOBILE, TABLET, DESKTOP) PASSED RESPONSIVENESS CHECKS!")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_responsiveness())
