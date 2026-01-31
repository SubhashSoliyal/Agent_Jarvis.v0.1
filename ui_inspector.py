
import asyncio
import os
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ui_inspector")

DATA_DIR = os.path.join(os.path.dirname(__file__), "backend", "Data")
STORY_DIR = os.path.join(DATA_DIR, "Stories")

async def inspect_ui():
    url = "https://aistudio.google.com/generate-speech?model=gemini-2.5-pro-preview-tts"
    
    async with async_playwright() as p:
        # Use persistent context to skip login if possible
        user_data_dir = os.path.join(DATA_DIR, "ChromeSession")
        try:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
        except:
             browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        try:
            logger.info(f"Navigating to {url}...")
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            
            # Wait for main UI
            try:
                await page.wait_for_selector("textarea", timeout=15000)
            except:
                logger.warning("Textarea not found immediately. Might be loading or login.")
            
            # Take screenshot of the initial state
            await page.screenshot(path=os.path.join(STORY_DIR, "ui_inspector_initial.png"))
            logger.info("Saved initial UI screenshot.")
            
            # Dump Buttons
            logger.info("--- BUTTONS ---")
            buttons = await page.query_selector_all("button")
            for i, btn in enumerate(buttons):
                try:
                    text = await btn.inner_text()
                    aria = await btn.get_attribute("aria-label") or ""
                    logger.info(f"Button {i}: Text='{text.strip()}', Aria='{aria}'")
                except: pass
            
            # Dump Dropdowns / Selects / Listboxes
            logger.info("--- DROPDOWNS / LISTBOXES ---")
            elements = await page.query_selector_all("[role='listbox'], select, [aria-haspopup='listbox'], [aria-haspopup='true']")
            for i, el in enumerate(elements):
                try:
                    text = await el.inner_text()
                    aria = await el.get_attribute("aria-label") or ""
                    role = await el.get_attribute("role") or ""
                    logger.info(f"Dropdown {i}: Role='{role}', Text='{text.strip()}', Aria='{aria}'")
                except: pass
                
            # Keep open for a moment to ensure user can see if needed
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Inspection failed: {e}")
            await page.screenshot(path=os.path.join(STORY_DIR, "ui_inspector_error.png"))
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_ui())
