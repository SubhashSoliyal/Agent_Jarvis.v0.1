import asyncio
import os
import sys
from playwright.async_api import async_playwright

# Add path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "Data", "WhatsApp_Profile")

async def main():
    print("--- WhatsApp Login Setup ---")
    print(f"Profile Path: {USER_DATA_DIR}")
    
    async with async_playwright() as p:
        print("Launching browser...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "web.whatsapp.com" not in page.url:
            await page.goto("https://web.whatsapp.com")
            
        print("\n" + "="*50)
        print("ACTION REQUIRED: Scan the QR Code now!")
        print("I will keep this window open until you are logged in.")
        print("="*50 + "\n")
        
        # Wait for Search Box (indicating login) with NO TIMEOUT
        try:
            await page.wait_for_selector('div[contenteditable="true"][data-tab="3"]', timeout=0)
            print("\n✅ Login Detected! Session saved.")
            print("You can now close the browser window manually, or wait 10 seconds.")
            await asyncio.sleep(10)
        except KeyboardInterrupt:
            print("User stopped the script.")
        
        await context.close()
        print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())
