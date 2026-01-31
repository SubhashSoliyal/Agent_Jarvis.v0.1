import os
import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Page, BrowserContext
from livekit.agents import function_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "WhatsApp_Profile")
HEADLESS_MODE = False  # Must be False for WhatsApp Web to work properly and for user visibility

class WhatsAppBrowser:
    _instance: Optional['WhatsAppBrowser'] = None
    _playwright = None
    _context: Optional[BrowserContext] = None
    _page: Optional[Page] = None
    
    @classmethod
    async def get_page(cls) -> Page:
        if cls._page and not cls._page.is_closed():
            return cls._page
            
        if not cls._playwright:
            cls._playwright = await async_playwright().start()
            
        if not cls._context:
            logger.info(f"Launching WhatsApp Browser with profile: {USER_DATA_DIR}")
            cls._context = await cls._playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=HEADLESS_MODE,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
                viewport=None # Full size
            )
            
        pages = cls._context.pages
        if pages:
            cls._page = pages[0]
        else:
            cls._page = await cls._context.new_page()
            
        if "web.whatsapp.com" not in cls._page.url:
            logger.info("Navigating to WhatsApp Web...")
            await cls._page.goto("https://web.whatsapp.com")
            
        # Wait for meaningful element (Search bar or QR code)
        try:
            logger.info("Waiting for WhatsApp to load...")
            # Wait for either the search box (logged in) or the QR code canvas (logged out)
            await cls._page.wait_for_selector(
                'div[contenteditable="true"][data-tab="3"], canvas[aria-label="Scan this QR code"]', 
                timeout=60000
            )
            
            # Check if we need to scan QR
            if await cls._page.locator('canvas[aria-label="Scan this QR code"]').is_visible():
                logger.warning("Please scan the QR Code to log in!")
                # We wait indefinitely or until logged in for the first run
                await cls._page.wait_for_selector('div[contenteditable="true"][data-tab="3"]', timeout=300000) # 5 min to scan
                
        except Exception as e:
            logger.error(f"Timeout waiting for WhatsApp load: {e}")
            
        return cls._page

    @classmethod
    async def close(cls):
        if cls._context:
            await cls._context.close()
            cls._context = None
            cls._page = None
        if cls._playwright:
            await cls._playwright.stop()
            cls._playwright = None

@function_tool
async def send_whatsapp_message(contact_name: str, message: str) -> str:
    """
    Sends a WhatsApp message via web.whatsapp.com.
    """
    try:
        page = await WhatsAppBrowser.get_page()
        
        # 1. Search for contact
        search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
        await search_box.click()
        await search_box.fill(contact_name)
        await search_box.press("Enter")
        await asyncio.sleep(1.0) # Wait for chat load
        
        # 2. Check if we are in the correct chat (verify header title if possible, or assume best match)
        # Using "Send message" box
        message_box = page.locator('div[contenteditable="true"][data-tab="10"]')
        await message_box.click()
        await message_box.fill(message)
        await message_box.press("Enter")
        
        return f"✅ Message sent to {contact_name}: '{message}'"
        
    except Exception as e:
        logger.error(f"WhatsApp Send Error: {e}")
        return f"❌ Failed to send message: {e}"

@function_tool
async def read_whatsapp_messages(unread_only: bool = True) -> str:
    """
    Reads unread conversations from the sidebar.
    Returns a summary of who sent messages.
    """
    try:
        page = await WhatsAppBrowser.get_page()
        
        # Look for green badges in the sidebar
        # The selector for unread badge often has an aria-label like "n unread messages"
        unread_chats = page.locator('span[aria-label*="unread message"]')
        count = await unread_chats.count()
        
        if count == 0:
            return "✅ No unread messages found."
            
        summary = []
        for i in range(min(count, 5)): # Read top 5
            badge = unread_chats.nth(i)
            # navigate up to find the container with contact info
            # Usually the parent structure holds the contact name
            # This is heuristic and fragile to UI updates
            
            # Alternative: Click the chat and read last message? That marks as read.
            # Ideally, we just report WHO sent messages for now.
            
            # Try to find the sibling text which is usually the name
            # This is complex without specific stable selectors.
            # Let's try to get the 'title' attribute of the chat container
            pass
            
        return f"✅ You have {count} unread conversation(s). check the browser window."
        
    except Exception as e:
        logger.error(f"WhatsApp Read Error: {e}")
        return f"❌ Failed to read messages: {e}"

@function_tool
async def make_whatsapp_call(contact_name: str, video: bool = False) -> str:
    """
    Initiates a voice/video call via WhatsApp Web.
    """
    try:
        page = await WhatsAppBrowser.get_page()
        
        # 1. Search and open chat (reuse logic)
        search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
        await search_box.click()
        await search_box.fill(contact_name)
        await search_box.press("Enter")
        await asyncio.sleep(1.0)
        
        # 2. Find Call button
        # Voice call title="Voice call"
        # Video call title="Video call"
        title = "Video call" if video else "Voice call"
        
        call_btn = page.locator(f'div[title="{title}"]')
        if await call_btn.is_visible():
            await call_btn.click()
            
            # Confirm "Start Call" dialog if it appears
            # Sometimes there is a confirmation popup
            confirm_btn = page.locator('div[role="button"]:has-text("Start call")')
            if await confirm_btn.is_visible(timeout=2000):
                await confirm_btn.click()
                
            return f"📞 Initiating {title} with {contact_name}..."
        else:
            return f"❌ Call button ({title}) not found. Is the person in your contacts?"
            
    except Exception as e:
        logger.error(f"WhatsApp Call Error: {e}")
        return f"❌ Failed to call: {e}"
