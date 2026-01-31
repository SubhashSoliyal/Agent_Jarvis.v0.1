import os
import aiohttp
import asyncio
import logging
from livekit.agents import function_tool
from playwright.async_api import async_playwright
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_safe_filename(name):
    """Sanitizes the filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

@function_tool
async def download_paper_or_document(url: str, name_or_topic: str) -> str:
    """
    Downloads a document from a URL. 
    If it's a direct file (PDF, etc.), it downloads it. 
    If it's a webpage, it saves the page as a PDF (Print representation).
    Saves to 'Downloads/Jarvis_Documents/{name_or_topic}/'.
    Opens the file after downloading.
    
    Args:
        url: The web link to download/save.
        name_or_topic: A short descriptive name for the file/topic (used for folder naming).
    """
    try:
        logger.info(f"⬇ Downloading {name_or_topic} from {url}")
        
        # 1. Prepare Directory
        safe_name = await get_safe_filename(name_or_topic)
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", "Jarvis_Documents", safe_name)
        
        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path)
            
        # 2. Check header or extension to decide method
        # Simple extension check first
        lower_url = url.lower()
        is_direct_file = any(lower_url.endswith(ext) for ext in ['.pdf', '.docx', '.doc', '.ppt', '.pptx', '.xls', '.xlsx', '.zip', '.txt'])
        
        file_path = ""
        
        if is_direct_file:
            # Direct Download
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        # Guess extension
                        if lower_url.endswith('.pdf'): ext = ".pdf"
                        elif lower_url.endswith('.docx'): ext = ".docx"
                        else: ext = os.path.splitext(url)[-1]
                        if len(ext) > 5: ext = ".pdf" # Fallback
                        
                        file_path = os.path.join(downloads_path, f"{safe_name}{ext}")
                        
                        with open(file_path, 'wb') as f:
                            f.write(await resp.read())
                        logger.info(f"✅ Direct download successful: {file_path}")
                    else:
                        logger.warning(f"⚠ Direct download failed (Status {resp.status}). Falling back to browser PDF.")
                        is_direct_file = False # Fallback to browser
        
        if not is_direct_file:
            # Webpage -> PDF via Playwright
            logger.info("🌍 Opening browser to capture page as PDF...")
            file_path = os.path.join(downloads_path, f"{safe_name}_Web.pdf")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                try:
                    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    # Give it a moment to render JS
                    await asyncio.sleep(2)
                    
                    # Save as PDF
                    await page.pdf(path=file_path, format="A4")
                    logger.info(f"✅ Webpage saved as PDF: {file_path}")
                except Exception as e:
                    logger.error(f"❌ Browser capture failed: {e}")
                    return f"❌ Failed to download or capture {url}: {e}"
                finally:
                    await browser.close()

        # 3. Open the file
        if os.path.exists(file_path):
            if os.name == 'nt':
                os.startfile(file_path)
            else:
                # Linux/Mac support just in case
                import subprocess
                subprocess.call(['xdg-open' if os.name == 'posix' else 'open', file_path])
                
            return f"✅ Document downloaded and opened!\nLocation: {file_path}"
        else:
            return "❌ Download appeared to succeed but file is missing."

    except Exception as e:
        logger.error(f"Download tool error: {e}")
        return f"❌ Error downloading document: {e}"
