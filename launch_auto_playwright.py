import sys

# Set encoding to UTF-8 to avoid UnicodeEncodeErrors
sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import subprocess
import time
import os
from playwright.async_api import async_playwright

# Data Directory for persistent session (Fresh Start to fix 404)
DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")
PLAYGROUND_SESSION_DIR = os.path.join(DATA_DIR, "PlaygroundSession_Clean")

if not os.path.exists(PLAYGROUND_SESSION_DIR):
    os.makedirs(PLAYGROUND_SESSION_DIR)

async def launch_and_connect():
    print("[*] Starting Jarvis Backend...")
    # Start the agent backend as a subprocess
    backend_process = subprocess.Popen(["python", "agent.py", "dev"], shell=True)
    
    # Wait for backend to initialize
    print("[*] Waiting for backend to initialize (5s)...")
    await asyncio.sleep(5)
    
    print("[*] Launching Browser (Persistent Session & Stealth)...")
    async with async_playwright() as p:
        # User Persistent Context with Stealth Args
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=PLAYGROUND_SESSION_DIR,
            channel="chrome", 
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled", 
                "--no-sandbox",
                "--disable-infobars"
            ],
            ignore_default_args=["--enable-automation"], # Hides 'Chrome is controlled by...'
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport=None
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        try:
            # STRATEGY: Login First to avoid "undefined" redirect loops
            print("[*] Navigating to LiveKit Cloud Login (to ensure valid session)...")
            await page.goto("https://cloud.livekit.io/login", timeout=60000)
            
            print("[*] Checking Login Status...")
            # Robust Login Check Loop
            max_retries = 60 # 60 * 2s = 2 mins wait (after initial check)
            logged_in = False
            
            for _ in range(max_retries):
                url = page.url
                content = await page.content()
                
                # Case 1: Already on Dashboard (Success)
                if "projects" in url or "application" in url:
                    print("[+] Dashboard detected! Logged in.")
                    logged_in = True
                    break
                
                # Case 2: User manually went to Playground (Success)
                if "agents-playground" in url:
                    print("[+] Playground detected! Logged in.")
                    logged_in = True
                    break
                    
                # Case 3: Still on Login Page
                if "Sign In" in await page.title() or await page.locator('input[type="password"]').count() > 0:
                    # Just wait
                    pass
                else:
                    # Maybe on some intermediate loading screen?
                    pass
                    
                await asyncio.sleep(2)
                
            if not logged_in:
                print("⚠ Login check timed out. Attempting to proceed anyway...")

            # Now go to Playground
            print("[*] Opening Agent Playground...")
            if "agents-playground" not in page.url:
                await page.goto("https://agents-playground.livekit.io/", timeout=60000)
            
            # Quick check for 404 just in case
            if "undefined" in page.url:
                 print("⚠ 404 still detected. Retrying navigation...")
                 await page.goto("https://agents-playground.livekit.io/", timeout=60000)

            # Wait for list of agents to load
            print("[*] Looking for 'jarvis' agent...")
            try:
                # Wait for the main container or list to be visible
                await page.wait_for_selector('div, button', timeout=15000)
                await asyncio.sleep(2) # Visual stability wait
            except:
                print("[!] Agent list slow to load...")

            # Select 'jarvis'
            print("[*] Attempting to select 'jarvis'...")
            try:
                # Strategy 1: Look for a list item or button with 'jarvis'
                # This is likely the agent card
                jarvis_card = page.locator('div[role="button"]:has-text("jarvis"), .agent-list-item:has-text("jarvis")').first
                
                if await jarvis_card.count() > 0:
                    print("[*] Found 'jarvis' card/button. Clicking...")
                    await jarvis_card.click()
                    await asyncio.sleep(0.5)
                else:
                    # Strategy 2: Text fallback (might hit a label, but worth a try)
                    print("[!] Specific card not found. Trying text fallback...")
                    await page.click('text="jarvis"', force=True)
            except Exception as e:
                 print(f"[-] Selection Error: {e}")

            await asyncio.sleep(2)

            # Persistent Connection Loop
            print("[*] Entering Persistence Connection Loop (Max 10 tries)...")
            for i in range(15):
                # 1. Check Success
                if await page.locator('text="Status" >> text="Connected"').count() > 0:
                     print("[+] SUCCESS: System is CONNECTED!")
                     break
                
                # 2. Find Candidates
                # Prioritize "Use jarvis", then "Connect", then generic submit
                candidates = page.locator('button:has-text("Use jarvis"), button:has-text("Connect"), button[type="submit"]')
                count = await candidates.count()
                
                print(f"[*] Attempt {i+1}: Found {count} buttons. Scanning...")
                
                if count > 0:
                    for idx in range(count):
                        btn = candidates.nth(idx)
                        if await btn.is_visible():
                            try:
                                txt = await btn.inner_text()
                                # Filter out irrelevant buttons if needed (e.g. Disconnect)
                                if "Disconnect" in txt: continue
                                
                                print(f"   > Clicking '{txt}'...")
                                # Method A: Playwright Click
                                try: await btn.click(force=True, timeout=500)
                                except: pass
                                
                                # Method B: JS Force Click (Bypasses overlays)
                                await btn.evaluate("b => b.click()")
                            except Exception as e:
                                print(f"   [-] Click failed: {e}")
                
                # 3. Check Header fallback
                header_btn = page.locator('header button:has-text("Connect")')
                if await header_btn.count() > 0 and await header_btn.is_visible():
                     print("   > Clicking Header Connect...")
                     await header_btn.evaluate("b => b.click()")

                await asyncio.sleep(2)

            print("[*] Automation complete. Monitoring session...")
            print("[*] NON-STOP MODE: Press Ctrl+C in this terminal to stop.")
            
            while True:
                if backend_process.poll() is not None:
                    print("[-] Backend process died. Exiting.")
                    break
                # Keep the script responsive
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"[-] Automation Error: {e}")
            await asyncio.sleep(20) # Keep open a bit to show error

if __name__ == "__main__":
    try:
        asyncio.run(launch_and_connect())
    except KeyboardInterrupt:
        print("\n[*] Jarvis Shutting Down.")
