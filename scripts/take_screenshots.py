import asyncio
from playwright.async_api import async_playwright
import os

async def take_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # Create screenshots directory if it doesn't exist
        screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'images')
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Navigate to dashboard
        await page.goto('http://localhost:3001')
        await page.wait_for_load_state('networkidle')
        
        # Take overview screenshot
        await page.screenshot(path=os.path.join(screenshots_dir, 'dashboard-overview.png'), full_page=False)
        
        # Screenshot epics section
        epics_section = page.locator('h2:has-text("Epics")')
        if await epics_section.count() > 0:
            await epics_section.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            await page.screenshot(path=os.path.join(screenshots_dir, 'dashboard-epics.png'), full_page=False)
        
        # Screenshot active agents section
        agents_section = page.locator('h2:has-text("Active Agents")')
        if await agents_section.count() > 0:
            await agents_section.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            await page.screenshot(path=os.path.join(screenshots_dir, 'dashboard-agents.png'), full_page=False)
        
        # Screenshot recent tasks section
        tasks_section = page.locator('h2:has-text("Recent Tasks")')
        if await tasks_section.count() > 0:
            await tasks_section.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            await page.screenshot(path=os.path.join(screenshots_dir, 'dashboard-tasks.png'), full_page=False)
        
        await browser.close()
        print("Screenshots saved to docs/images/")

if __name__ == "__main__":
    asyncio.run(take_screenshots())