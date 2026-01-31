import asyncio
import os
import sys
from playwright.async_api import async_playwright

# Add path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "Data", "WhatsApp_Profile")

async def main():
    print("--- WhatsApp Selector Debug ---")
    async with async_playwright() as p:
        print(f"Launching browser (Profile: {USER_DATA_DIR})...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "web.whatsapp.com" not in page.url:
            await page.goto("https://web.whatsapp.com")
            
        print("Waiting for page load (60s)... Please Scan QR if needed!")
        
        # Try to find ANY recognizable element
        try:
            # Wait for something that indicates load (Search box OR Chat list OR QR canvas)
            await page.wait_for_selector('div[contenteditable="true"], canvas', timeout=60000)
            print("Page loaded something.")
            
            # 1. Search Box Candidates
            print("Checking Search Box selectors...")
            selectors = [
                 'div[contenteditable="true"][data-tab="3"]',
                 'div[contenteditable="true"][aria-label="Search"]',
                 'div[contenteditable="true"][aria-label="Search input textbox"]',
                 'div[role="textbox"][aria-label="Search"]',
                 'p.selectable-text.copyable-text' # Common class for text inputs
            ]
            
            found_search = False
            for sel in selectors:
                count = await page.locator(sel).count()
                if count > 0:
                    print(f"✅ Found candidate selector: {sel} (Count: {count})")
                    # Try to focus it to see if it's the right one
                    if not found_search:
                        try:
                            await page.locator(sel).first.click(timeout=2000)
                            print(f"   -> Clicked successfully.")
                            found_search = True
                        except:
                            print(f"   -> Click failed.")
                else:
                    print(f"❌ Selector not found: {sel}")
            
            if found_search:
                print("Typing 'ruchi'...")
                await page.keyboard.type("ruchi")
                await asyncio.sleep(2)
                print("Check if results appeared.")
            else:
                print("CRITICAL: No search box found. WhatsApp UI might have changed or not logged in.")

        except Exception as e:
            print(f"Error during check: {e}")
            
        await asyncio.sleep(10) # Give user time to see
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
