import os
import asyncio
import logging
from livekit.agents import function_tool
from playwright.async_api import async_playwright
from backend.Jarvis_utils import clean_browser_user_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data Directory for persistent session
DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")
TESTBOOK_SESSION_DIR = os.path.join(DATA_DIR, "TestbookSession")

if not os.path.exists(TESTBOOK_SESSION_DIR):
    os.makedirs(TESTBOOK_SESSION_DIR)

@function_tool
async def automate_testbook(action: str, query: str = "") -> str:
    """
    Automates interactions with Testbook.com.
    
    Args:
        action: The action to perform. Options:
            - "login": Log in to Testbook (uses Env vars if available, else waits for user).
            - "search": Search for a test/exam (e.g., "SSC CGL", "Banking").
            - "dashboard": navigate to user's dashboard/pass page.
        query: The search term (required for 'search' action).
    """
    logger.info(f"Testbook Automation: Action={action}, Query={query}")
    
    clean_browser_user_data(TESTBOOK_SESSION_DIR)
    
    async with async_playwright() as p:
        try:
            logger.info("Launching Browser for Testbook...")
            # Launch with persistent context to save login state
            # Enhanced for stability: ignore HTTPS errors, sets user agent
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=TESTBOOK_SESSION_DIR,
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = browser.pages[0] if browser.pages else await browser.new_page()
            
            # Helper for robust navigation with retry
            async def navigate_with_retry(url, retries=3):
                for i in range(retries):
                    try:
                        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                        return True
                    except Exception as e:
                        logger.warning(f"Navigation to {url} failed (Attempt {i+1}/{retries}): {e}")
                        await asyncio.sleep(2)
                return False

            # Navigate based on action
            if action == "login":
                if not await navigate_with_retry("https://testbook.com/"):
                    return "❌ Failed to load Testbook.com after multiple retries. Network might be down."
                
                logger.info("Opened Testbook. Checking login state...")
                
                # Check if already logged in (look for avatar/dashboard link)
                # This selector is a guess, needs adjustment based on actual site
                if await page.locator('a[href*="/dashboard"]').count() > 0 or \
                   await page.locator('.user-profile').count() > 0:
                    return "✅ Already logged in to Testbook."
                
                # Click Login
                login_btn = page.locator('a:has-text("Login"), button:has-text("Login")').first
                if await login_btn.count() > 0:
                    await login_btn.click()
                    logger.info("Clicked Login. Waiting for user input or credentials...")
                    
                    # Try to fill from ENV if available
                    phone = os.getenv("TESTBOOK_PHONE")
                    password = os.getenv("TESTBOOK_PASSWORD")
                    
                    if phone:
                        # Common selector for phone/email
                        inp = page.locator('input[type="text"], input[type="tel"], input[type="email"]').first
                        if await inp.count() > 0:
                            await inp.fill(phone)
                            logger.info("Filled Phone/Email.")
                    
                    # Wait for user to complete login (OTP etc)
                    logger.info("Waiting 60s for user to complete login manually if needed...")
                    try:
                        await page.wait_for_url("**/dashboard**", timeout=60000)
                        return "✅ Login Successful! Dashboard detected."
                    except:
                        return "⚠ Login timed out or manual step required. Browser is open."

            elif action == "search":
                if not query:
                    return "❌ Query is required for search."
                
                if not await navigate_with_retry("https://testbook.com/"):
                     return "❌ Failed to load Testbook search page."
                
                await asyncio.sleep(2)
                
                # Find search bar - Try multiple common selectors
                search_input = page.locator('input[placeholder*="Search"], input[type="search"], input[data-cy*="search"]').first
                if await search_input.count() > 0:
                    try:
                        await search_input.click()
                        await search_input.fill(query)
                        await page.keyboard.press('Enter')
                        logger.info(f"Searched for {query}")
                        
                        # Wait for results or 'Test Series' tab
                        await page.wait_for_selector('a[href*="/test-series"], .search-results', timeout=10000)
                        return f"✅ Search results for '{query}' are now visible."
                    except Exception as e:
                         return f"⚠ Found search bar but failed to interact: {e}"
                else:
                    return "❌ Could not find search bar (Selectors failed)."

            elif action == "dashboard":
                if await navigate_with_retry("https://testbook.com/dashboard"):
                    return "✅ Opened Dashboard."
                else:
                    return "❌ Failed to open Dashboard."
            
            elif action == "save_work":
                if await navigate_with_retry("https://testbook.com/dashboard"):
                    logger.info("Navigated to Dashboard for saving work.")
                else:
                    return "❌ Failed to reach Dashboard for saving work."
                
                saved_questions_dir = os.path.join(DATA_DIR, "Testbook_Saves")
                if not os.path.exists(saved_questions_dir):
                    os.makedirs(saved_questions_dir)
                
                # Try to find "Attempted Tests" or "Saved" section
                # Selector guesses based on common dashboard layouts
                try:
                    # Look for 'Saved Questions' or similar link
                    saved_link = page.locator('a:has-text("Saved Questions"), a[href*="saved-questions"]').first
                    if await saved_link.count() > 0:
                        await saved_link.click()
                        await page.wait_for_load_state('networkidle')
                        
                        # Save Page as PDF
                        pdf_path = os.path.join(saved_questions_dir, "Saved_Questions.pdf")
                        await page.pdf(path=pdf_path)
                        logger.info(f"Saved PDF to {pdf_path}")
                        return f"✅ Saved Questions downloaded to: {pdf_path}"
                    
                    # Fallback: Attempted Tests
                    attempted_link = page.locator('a:has-text("Attempted"), a[href*="attempted"]').first
                    if await attempted_link.count() > 0:
                        await attempted_link.click()
                        await page.wait_for_load_state('networkidle')
                        
                        pdf_path = os.path.join(saved_questions_dir, "Attempted_Tests.pdf")
                        await page.pdf(path=pdf_path)
                        return f"✅ Attempted Tests list saved to: {pdf_path}"
                        
                    return "⚠ Could not find 'Saved Questions' or 'Attempted' section. Screenshots/PDF saved for Dashboard."
                    
                except Exception as e:
                    # Last resort: Screenshot dashboard
                    ss_path = os.path.join(saved_questions_dir, "Dashboard_Snapshot.png")
                    await page.screenshot(path=ss_path, full_page=True)
                    return f"⚠ Scrape partial. Dashboard snapshot saved: {ss_path} (Error: {e})"

            else:
                return f"❌ Unknown action: {action}"

            # Keep open for a bit if we just did a simple action
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Testbook Error: {e}")
            return f"❌ Error: {e}"
        finally:
            # We usually close the browser, but for automation we might want to keep session data
            if 'browser' in locals():
                await browser.close()

    return "✅ Action completed."
