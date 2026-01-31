import os
import asyncio
import logging
from docx import Document
from livekit.agents import function_tool
from playwright.async_api import async_playwright
from backend.Jarvis_prompts import personal_context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from backend.Jarvis_utils import save_formatted_doc, clean_browser_user_data

# Ensure Reports directory exists
DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")
REPORTS_DIR = os.path.join(DATA_DIR, "Reports")
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

# DeepSeek Credentials (Using .env as requested)
DS_EMAIL = os.getenv("GOOGLE_EMAIL")
DS_PASS = os.getenv("GOOGLE_PASSWORD")

if not DS_EMAIL or not DS_PASS:
    logger.warning("DeepSeek credentials not found in .env (GOOGLE_EMAIL/GOOGLE_PASSWORD). Automation may fail.")

@function_tool
async def generate_deepseek_report(topic: str) -> str:
    """
    Generates a detailed, professional report or article on ANY topic using DeepSeek's AI.
    Use this tool whenever the user asks for a "report", "document", "deep research", or "long-form writing".
    This tool opens a browser, performs the research/writing, and saves it as a Word (.docx) file.
    """
    logger.info(f"Generating report on: {topic}")
    
    logger.info(f"Generating report on: {topic}")
    
    async with async_playwright() as p:
        # --- Secure Browser Launch ---
        user_data_dir = os.path.join(DATA_DIR, "DeepSeekSession")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

        clean_browser_user_data(user_data_dir)

        try:
            logger.info("Launching Chrome with persistent context...")
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
        except:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        try:
            # 1. Navigate to Chat (Skip Login if possible)
            logger.info("Navigating to DeepSeek...")
            await page.goto("https://chat.deepseek.com/")
            
            # Check if login is needed (URL redirect OR visible login elements)
            # Give it a moment to settle
            await asyncio.sleep(3.0)
            
            # Case A: We are on the landing page but need to click "Log in"
            # Look for a button that specifically says "Log in"
            # Updated selectors for robustness
            login_btn = page.locator('div[role="button"]:has-text("Log in"), button:has-text("Log in"), div:has-text("Log in")').first
            if await login_btn.count() > 0 and await login_btn.is_visible():
                 logger.info("Found 'Log in' button. Clicking...")
                 await login_btn.click()
                 await asyncio.sleep(2.0)

            # Case B: We are on a login page (URL contains 'login' or password field visible)
            if "login" in page.url or await page.locator('input[type="password"]').count() > 0:
                logger.info("Login required. Attempting auto-login...")
                try:
                     # 1. Fill Email (try different selectors)
                     email_input = page.locator('input[type="text"], input[type="email"], input[placeholder*="Email"]').first
                     if await email_input.count() > 0:
                         logger.info(f"Filling email: {DS_EMAIL[:3]}***")
                         await email_input.fill(DS_EMAIL)
                     
                     # 2. Fill Password
                     pass_input = page.locator('input[type="password"]').first
                     if await pass_input.count() > 0:
                         logger.info("Filling password...")
                         await pass_input.fill(DS_PASS)
                     
                     # 3. Check for specific "checkbox" (Terms) if any, but usually not for login
                     
                     # 4. Click Log In/Sign In
                     # Try to match the submit button
                     submit_btn = page.locator('button[type="submit"], button:has-text("Log in"), div[role="button"]:has-text("Log in")').last
                     if await submit_btn.count() > 0:
                         logger.info("Clicking Submit/Login...")
                         await submit_btn.click()
                     
                     # Wait for redirect
                     await page.wait_for_url("https://chat.deepseek.com/**", timeout=45000) # Increased timeout
                     logger.info("Login submitted. Waiting for chat...")

                except Exception as e:
                    logger.warning(f"Auto-login skipped or failed: {e}")
            
            # Wait for chat interface
            logger.info("Waiting for chat interface...")
            await page.wait_for_selector('textarea', timeout=60000)
            
            # --- Enable DeepThink (R1) and Search (Web) ---
            logger.info("Enabling DeepThink and Search...")
            
            # Define Button Locators
            # We use text filtering to be robust against order changes
            btn_deepthink = page.locator('.ds-toggle-button').filter(has_text="DeepThink")
            btn_search = page.locator('.ds-toggle-button').filter(has_text="Search")
            
            # Helper to toggle on
            async def ensure_active(btn, name):
                try:
                    if await btn.count() > 0:
                        # Check if active
                        classes = await btn.get_attribute('class')
                        if 'ds-toggle-button--selected' not in classes:
                            logger.info(f"Activating {name}...")
                            await btn.click()
                            # Wait for it to become active
                            try:
                                await btn.wait_for(state="visible") # Ensure generic visibility
                                # Optional: verify class change? 
                                # DeepSeek might take a ms to update class.
                                await asyncio.sleep(0.5)
                            except:
                                pass
                        else:
                            logger.info(f"{name} is already active.")
                    else:
                        logger.warning(f"{name} button not found.")
                except Exception as e:
                    logger.warning(f"Failed to toggle {name}: {e}")

            await ensure_active(btn_deepthink, "DeepThink")
            await ensure_active(btn_search, "Search")
            
            # --- Step 1: Initial Context & Draft ---
            logger.info("Sending Step 1 Prompt (Initial Draft)...")
            prompt_1 = f"Context: {personal_context}. I need a comprehensive, high-quality report on '{topic}'. First, create a structured outline identifying key sections, advanced technical concepts, and core arguments. Ensure the foundation is solid for a professional deep-dive."
            await page.fill('textarea', prompt_1)
            await page.keyboard.press('Enter')
            
            # Wait for Step 1 generation
            await wait_for_generation(page, "step_1")

            # --- Step 2: Final Comprehensive Report with Formulas ---
            logger.info("Sending Step 2 Prompt (Deep Refinement)...")
            # Step 2: Refinement (The "Deep" part)
            # We ask for a "Markdown Code Block" to get raw tables and formulas.
            # CRITICAL: We explicitly forbid "vertical lists" for variables to prevent the layout issue.
            refinement_prompt = (
                "Great. Now, write the **FINAL COMPREHENSIVE REPORT** based on that draft. "
                "1.  **Depth & Length:** Expand significantly (aim for 5000+ words). Deep-dive into technical details.\n"
                "2.  **Structure:** Include an **Executive Summary** at the start and **Real-world Case Studies**.\n"
                "3.  **Data:** Include a **Detailed Table** comparing key concepts or data.\n"
                "4.  **Math:** Use **Mathematical Formulations** (e.g., $$ E=mc^2 $$) where appropriate.\n"
                "5.  **Formatting**: When defining variables, keep them on ONE LINE or use a Table. Avoid vertical lists for simple definitions.\n"
                "6.  **References:** Add a 'References' section with credible sources.\n"
                "7.  **CRITICAL OUTPUT FORMAT**: Provide the entire report inside a SINGLE MARKDOWN CODE BLOCK (```markdown ... ```). "
            )
            
            # Focus textarea again if needed (DeepSeek usually keeps focus, but safety first)
            await page.click('textarea') 
            await page.fill('textarea', refinement_prompt)
            await page.keyboard.press('Enter')
            
            # Wait for Step 2 generation (The Final Result)
            await wait_for_generation(page, "step_2")

            # Scrape content (Priority: RAW Code Blocks via <pre>)
            report_content = ""
            
            # 1. Try to find the Markdown Code Block (in a <pre> tag)
            pre_elements = await page.query_selector_all('pre')
            if pre_elements:
                logger.info("Found pre blocks (Code). Scraping raw markdown...")
                try:
                    # Try to get code element specifically to avoid headers like "Copy Download"
                    code_el = await pre_elements[-1].query_selector('code')
                    if code_el:
                        report_content = await code_el.inner_text()
                    else:
                        report_content = await pre_elements[-1].inner_text()
                except Exception as e:
                    logger.warning(f"Failed to access pre block: {e}")
                    report_content = ""
            
            # Retry scraping loop to handle stale elements
            for attempt in range(5):
                try:
                    # Refresh elements list on every attempt
                    elements = await page.query_selector_all('.ds-markdown')
                    if not elements:
                        elements = await page.query_selector_all('div[class*="markdown"]')
                    
                    if elements:
                        max_len = 0
                        for el in elements:
                            try:
                                text = await el.inner_text()
                                if len(text) > max_len:
                                    max_len = len(text)
                                    report_content = text
                            except:
                                continue # Single element fail, try others
                        
                        if len(report_content) > 200:
                            logger.info(f"Scraped longest block: {max_len} chars")
                            break # Success
                        
                    await asyncio.sleep(1.0) # Wait before retry
                except Exception as e:
                    logger.warning(f"Scraping attempt {attempt} failed: {e}")
                    await asyncio.sleep(1.0)

            # Fallback: Content is still too short (maybe failed?)
            if not report_content or len(report_content) < 200:
                 logger.warning("Main scraping failed or too short. Trying catch-all strategy.")
                 frames = await page.query_selector_all('.ds-chat-item') 
                 if frames:
                     # Check the last few frames
                     for frame in reversed(frames):
                         text = await frame.inner_text()
                         if len(text) > 200:
                             report_content = text
                             break
                     if not report_content:
                        report_content = await frames[-1].inner_text()
                 else:
                     report_content = await page.inner_text('body')

            if not report_content or len(report_content) < 100:
                logger.error(f"Scraping failed completely. Content: {report_content[:100]}")
                return f"❌ Failed to scrape report. The AI generated text, but I couldn't copy it. Found {len(report_content)} chars."
            
            # 5. Organization: Create Topic Subdirectory
            safe_topic = topic.replace(' ', '_')
            TOPIC_DIR = os.path.join(REPORTS_DIR, safe_topic)
            if not os.path.exists(TOPIC_DIR):
                os.makedirs(TOPIC_DIR)
            
            # Update paths to point to TOPIC_DIR
            doc_path = os.path.join(TOPIC_DIR, f"{safe_topic}_Report.docx")
            doc_path = os.path.abspath(doc_path)
            
            # DEBUG: Save exact raw content
            raw_path = os.path.join(TOPIC_DIR, f"{safe_topic}_RAW.txt")
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"DEBUG: Saved raw content to {raw_path}")

            # --- Save as Markdown (.md) ---
            md_path = os.path.join(TOPIC_DIR, f"{safe_topic}_Report.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"Markdown report saved to {md_path}")
            
            save_formatted_doc(report_content, doc_path, topic)
            
            logger.info(f"Report saved to {doc_path} ({len(report_content)} chars)")
            
            # --- Step 3: LaTeX Conversion ---
            # Using a more forceful prompt to ensure completeness and minimal wasted tokens
            logger.info("Sending Step 3 Prompt (LaTeX Conversion)...")
            latex_prompt = (
                "Excellent. Now, convert this **ENTIRE REPORT** into a single, valid **LaTeX (.tex)** file. "
                "CRITICAL INSTRUCTIONS:\n"
                "1. **Use `tabularx`:** For ALL tables, MUST use `\\usepackage{tabularx}` in preamble and `\\begin{tabularx}{\\textwidth}{...}` for the environment. Use `X` type columns for descriptions/text to ensure proper wrapping and preventing overflow.\n"
                "2. **Justification:** Ensure text is fully justified. Include `\\usepackage{microtype}` in preamble.\n"
                "3. **Table Safety:** Check that every table row has EXACTLY (Columns - 1) ampersands (&). Never have more cells than defined columns.\n"
                "4. **Completeness:** The output MUST BE COMPLETE. Do not truncate the code. Provide ONLY the LaTeX code in a single block."
            )
            await page.click('textarea') 
            await page.fill('textarea', latex_prompt)
            await page.keyboard.press('Enter')
            
            await wait_for_generation(page, "step_3_latex")
            
            # Scrape LaTeX (Re-using robust logic)
            latex_content = ""
            pre_elements = await page.query_selector_all('pre')
            if pre_elements:
                try:
                    code_el = await pre_elements[-1].query_selector('code')
                    if code_el:
                         latex_content = await code_el.inner_text()
                    else:
                         latex_content = await pre_elements[-1].inner_text()
                except:
                    pass
            
            if not latex_content:
                # Fallback Loop
                for attempt in range(5):
                    try:
                        elements = await page.query_selector_all('.ds-markdown')
                        if not elements:
                             elements = await page.query_selector_all('div[class*="markdown"]')
                        if elements:
                            max_len = 0
                            for el in elements:
                                try:
                                    text = await el.inner_text()
                                    if len(text) > max_len:
                                        max_len = len(text)
                                        latex_content = text
                                except: continue
                            if len(latex_content) > 200: break
                        await asyncio.sleep(1.0)
                    except: await asyncio.sleep(1.0)

            # Save LaTeX
            tex_path = os.path.join(TOPIC_DIR, f"{safe_topic}_Report.tex")
            if latex_content:
                # Cleanup markdown markers just in case
                latex_content = latex_content.replace("```latex", "").replace("```", "").strip()
                with open(tex_path, "w", encoding="utf-8") as f:
                    f.write(latex_content)
                logger.info(f"LaTeX report saved to {tex_path}")
            else:
                logger.warning("Failed to scrape LaTeX content.")

            # Post-save buffer to allow OS file system updates
            await asyncio.sleep(1.0) 
            
            # 6. Open File (Verify existence first with retry)
            for _ in range(3):
                if os.path.exists(doc_path):
                    break
                await asyncio.sleep(1.0)
                
            if os.path.exists(doc_path):
                logger.info(f"Opening report: {doc_path}")
                os.startfile(doc_path)
                
                conclusion = extract_conclusion(report_content)
                msg = (f"✅ Report Bundle Generated!\n"
                        f"1. Docx: file:///{doc_path.replace(os.sep, '/')}\n"
                        f"2. Markdown: file:///{md_path.replace(os.sep, '/')}\n"
                        f"3. LaTeX: file:///{tex_path.replace(os.sep, '/')}")
                
                if conclusion:
                    msg += f"\n\n🎓 **Conclusion Overview:**\n{conclusion}"
                
                return msg
            else:
                logger.error(f"File was saved but not found at: {doc_path}")
                return f"✅ Report generated but could not be opened. Path: {doc_path}"

        except Exception as e:
            logger.error(f"DeepSeek automation failed: {e}")
            try:
                await page.screenshot(path=os.path.join(DATA_DIR, "error_screenshot.png"))
            except:
                pass
            return f"❌ Report generation failed: {e}"
            
        finally:
            await browser.close()

@function_tool
async def generate_deepseek_content(topic: str, content_type: str = "general") -> str:
    """
    Generates content using DeepSeek (https://chat.deepseek.com/).
    Useful for emails, essays, stories, or coding tasks where DeepSeek's reasoning might help.
    Unlike 'generate_deepseek_report', this tool does NOT perform multi-step research.
    
    Args:
        topic: The subject or instruction (e.g., "Write an email to...").
        content_type: The type of content (e.g., "Email", "Essay").
    """
    logger.info(f"Generating {content_type} on: {topic} using DeepSeek")
    
    async with async_playwright() as p:
        # --- Secure Browser Launch ---
        user_data_dir = os.path.join(DATA_DIR, "DeepSeekSession")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

        clean_browser_user_data(user_data_dir)

        try:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
        except:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        try:
            # 1. Login (Reusing logic)
            logger.info("Navigating to DeepSeek...")
            await page.goto("https://chat.deepseek.com/")
            
            # Check if login is needed (URL redirect OR visible login elements)
            await asyncio.sleep(3.0)
            
            # Case A: We are on the landing page but need to click "Log in"
            login_btn = page.locator('div[role="button"]:has-text("Log in"), button:has-text("Log in")').first
            if await login_btn.count() > 0 and await login_btn.is_visible():
                 await login_btn.click()
                 await asyncio.sleep(2.0)

            # Case B: We are on a login page
            if "login" in page.url or await page.locator('input[type="password"]').count() > 0:
                try:
                     email_input = page.locator('input[type="text"], input[type="email"], input[placeholder*="Email"]').first
                     if await email_input.count() > 0:
                         await email_input.fill(DS_EMAIL)
                     
                     pass_input = page.locator('input[type="password"]').first
                     if await pass_input.count() > 0:
                         await pass_input.fill(DS_PASS)
                     
                     submit_btn = page.locator('button[type="submit"], button:has-text("Log in"), div[role="button"]:has-text("Log in")').last
                     if await submit_btn.count() > 0:
                         await submit_btn.click()
                except:
                    pass 

            # Wait for chat
            logger.info("Waiting for chat interface...")
            await page.wait_for_selector('textarea', timeout=30000)
            
            # 2. Configure (Disable DeepThink/Search for simple content if possible to save time)
            # Actually, DeepSeek R1 is great, let's keep DeepThink ON if it's there, but maybe Search isn't needed for an email.
            # Let's default to just ensuring the UI is ready.
            
            # 3. Send Prompt
            prompt = (
                f"Use this personal context for the author/user: {personal_context}\n"
                f"Write a {content_type} about '{topic}'. "
                "Do not include any 'Sure' or 'Here is' preamble. "
                "Start directly with the content. "
                "Format it nicely with Markdown."
            )
            await page.fill('textarea', prompt)
            await page.keyboard.press('Enter')
            
            # 4. Wait for generation
            # Reusing wait helper
            await wait_for_generation(page, "content_generation")
            
            # 5. Scrape
            content = ""
            elements = await page.query_selector_all('.ds-markdown')
            if not elements:
                 elements = await page.query_selector_all('div[class*="markdown"]')
            
            if elements:
                content = await elements[-1].inner_text()
            
            if not content: 
                 content = await page.inner_text('.ds-chat-item:last-child')

            if content:
                # Save
                CONTENT_DIR = os.path.join(DATA_DIR, "Content") # Ensure we point to Content dir not Reports
                if not os.path.exists(CONTENT_DIR): os.makedirs(CONTENT_DIR)
                
                safe_topic = topic.replace(" ", "_").replace("'", "")[:50]
                doc_path = os.path.join(CONTENT_DIR, f"{safe_topic}_DeepSeek.docx")
                
                # Save Markdown too
                with open(os.path.join(CONTENT_DIR, f"{safe_topic}_DeepSeek.md"), "w", encoding="utf-8") as f:
                    f.write(content)
                    
                save_formatted_doc(content, doc_path, topic)
                
                if os.path.exists(doc_path):
                     os.startfile(doc_path)
                     return f"✅ Content Generated via DeepSeek!\nSaved to: {doc_path}"
                else:
                     return "❌ Failed to save document."
            else:
                return "❌ Failed to scrape content from DeepSeek."

        except Exception as e:
            logger.error(f"DeepSeek Content Error: {e}")
            return f"❌ DeepSeek Error: {e}"
        finally:
            await browser.close()

from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re

from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re



@function_tool
async def generate_deepseek_research_paper(topic: str) -> str:
    """
    Generates a formal ACADEMIC RESEARCH PAPER on a topic.
    This differs from a 'report' by strictly following academic structure:
    Abstract, Introduction, Related Work, Methodology, Results/Discussion, Conclusion, References.
    It produces both a Word Doc and a LaTeX file tailored for academic submission.
    """
    logger.info(f"Generating Research Paper on: {topic}")
    
    async with async_playwright() as p:
        # --- Secure Browser Launch ---
        user_data_dir = os.path.join(DATA_DIR, "DeepSeekSession")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

        clean_browser_user_data(user_data_dir)

        try:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
        except:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        try:
            # 1. Login
            await page.goto("https://chat.deepseek.com/")
            # Check if login is needed (URL redirect OR visible login elements)
            await asyncio.sleep(3.0)
            
            login_btn = page.locator('div[role="button"]:has-text("Log in"), button:has-text("Log in")').first
            if await login_btn.count() > 0 and await login_btn.is_visible():
                 await login_btn.click()
                 await asyncio.sleep(2.0)

            if "login" in page.url or await page.locator('input[type="password"]').count() > 0:
                try:
                     email_input = page.locator('input[type="text"], input[type="email"], input[placeholder*="Email"]').first
                     if await email_input.count() > 0: await email_input.fill(DS_EMAIL)
                     pass_input = page.locator('input[type="password"]').first
                     if await pass_input.count() > 0: await pass_input.fill(DS_PASS)
                     submit_btn = page.locator('button[type="submit"], button:has-text("Log in"), div[role="button"]:has-text("Log in")').last
                     if await submit_btn.count() > 0: await submit_btn.click()
                except: pass

            logger.info("Waiting for chat...")
            await page.wait_for_selector('textarea', timeout=30000)
            
            # Enable DeepThink
            # Enable DeepThink AND Search
            btn_deepthink = page.locator('.ds-toggle-button').filter(has_text="DeepThink")
            btn_search = page.locator('.ds-toggle-button').filter(has_text="Search")

            async def ensure_active(btn):
                if await btn.count() > 0:
                    classes = await btn.get_attribute('class')
                    if 'ds-toggle-button--selected' not in classes:
                        await btn.click()
                        await asyncio.sleep(0.5)

            await ensure_active(btn_deepthink)
            await ensure_active(btn_search)

            # --- Step 1: Research & Outline ---
            logger.info("Phase 1: Research & Outline...")
            prompt_1 = (
                f"Author Context: {personal_context}. "
                f"You are an expert academic researcher. I need a rigorous, publication-ready Research Paper on '{topic}'. "
                "First, conduct a deep analysis of key literature, methodologies, and findings. "
                "Output a structured outline including: \n"
                "1. **Abstract** & **Novelty Statement** (what is new?).\n"
                "2. **Introduction** & **Problem Formulation**.\n"
                "3. **Literature Review** (identify gaps).\n"
                "4. **Methodology** (mathematical/algorithmic depth).\n"
                "5. **Results** (simulated/theoretical).\n"
                "6. **Conclusion**.\n"
                "7. **Preliminary Bibliography**."
            )
            await page.fill('textarea', prompt_1)
            await page.keyboard.press('Enter')
            await wait_for_generation(page, "paper_outline")

            # --- Step 2: Full Academic Writing ---
            logger.info("Phase 2: Writing Full Content...")
            writing_prompt = (
                "Now, write the **FULL ACADEMIC PAPER** based on that outline. "
                "1. **Tone:** Strict academic, objective, third-person. Use Ph.D. level vocabulary and sentence structure.\n"
                "2. **Structure:** \n"
                "   - **Abstract**: Concise, impactful summary.\n"
                "   - **1. Introduction**: Clear motivation and contribution.\n"
                "   - **2. Related Work**: Comprehensive review.\n"
                "   - **3. Methodology**: RIGOROUS mathematical modeling and algorithmic descriptions.\n"
                "   - **4. Results**: Quantitative findings (simulate data if needed), use **Tables** and **Charts** (described in text).\n"
                "   - **5. Conclusion**.\n"
                "   - **References** . \n"
                "     - Format: [1] A. B. Author, \"Title of paper,\" *Abbrev. Title of Journal*, vol. x, no. x, pp. xxx-xxx, Abbrev. Month, Year.\n"
                "     - **CITATION IN TEXT**: You MUST cite these using [1], [2], etc. throughout the text.\n"
                "3. **Length:** Comprehensive (aim for 5000+ words equivalent content).\n"
                "4. **Format:** Output inside a single Markdown Code Block."
            )
            await page.fill('textarea', writing_prompt)
            await page.keyboard.press('Enter')
            await wait_for_generation(page, "paper_content")

            # Scrape Content
            content = ""
            elements = await page.query_selector_all('.ds-markdown')
            if not elements: elements = await page.query_selector_all('div[class*="markdown"]')
            if elements: content = await elements[-1].inner_text()
            
            if not content:
                 return "❌ Failed to generate paper content."

            # Save Docx/MD
            safe_topic = topic.replace(" ", "_")[:30]
            PAPER_DIR = os.path.join(REPORTS_DIR, safe_topic + "_Paper")
            if not os.path.exists(PAPER_DIR): os.makedirs(PAPER_DIR)
            
            doc_path = os.path.join(PAPER_DIR, f"{safe_topic}_ResearchPaper.docx")
            md_path = os.path.join(PAPER_DIR, f"{safe_topic}_ResearchPaper.md")
            
            with open(md_path, "w", encoding="utf-8") as f: f.write(content)
            save_formatted_doc(content, doc_path, topic)

            # --- Step 3: Proper LaTeX ---
            logger.info("Phase 3: LaTeX Formatting...")
            latex_prompt = (
                "Convert this paper into a **professional LaTeX** format (use `article`, double column if appropriate, or standard). "
                "CRITICAL REQUIREMENTS:\n"
                "1. **Tables:** Use `\\usepackage{tabularx}`. Use `\\small` font size inside tables. Ensure strict `&` column limits.\n"
                "2. **Figures:** Use `\\usepackage{float}` and place figures with `[H]`. Use `[width=\\linewidth]`.\n"
                "3. **Justification:** Use `\\usepackage{microtype}` and `\\usepackage[margin=1in]{geometry}`.\n"
                "4. **Completeness:** IF THE CODE IS LONG, I WILL ASK YOU TO 'CONTINUE'. Do not summarize.\n"
                "5. **Output:** Provide ONLY the valid LaTeX code in a block."
            )
            await page.fill('textarea', latex_prompt)
            await page.keyboard.press('Enter')
            await wait_for_generation(page, "paper_latex")
            
            # Scrape LaTeX with Continue Logic
            latex_code = ""
            full_latex_code = ""
            
            for _ in range(5): # Max 5 continuations to prevent infinite loops
                # Scrape current block
                pre_elements = await page.query_selector_all('pre')
                if pre_elements:
                    try:
                        # Get the last code block (newest)
                        code_el = await pre_elements[-1].query_selector('code')
                        if code_el: 
                            chunk = await code_el.inner_text()
                        else: 
                            chunk = await pre_elements[-1].inner_text()
                        
                        # Clean chunk
                        chunk = chunk.replace("```latex", "").replace("```", "").strip()
                        
                        # Heuristic: If this chunk is just a repetition of the start, don't append. 
                        # But DeepSeek usually appends. Actually, if we ask "Continue", it gives the *next* part.
                        # So we append.
                        
                        if chunk not in full_latex_code:
                             full_latex_code += "\n" + chunk
                        
                    except: pass
                
                # Check for completion
                if "\\end{document}" in full_latex_code:
                    logger.info("LaTeX completion detected.")
                    break
                else:
                    logger.info("LaTeX incomplete. Requesting continuation...")
                    await page.fill('textarea', "Continue generating the LaTeX code from where you stopped. Output ONLY the code.")
                    await page.keyboard.press('Enter')
                    await wait_for_generation(page, f"paper_latex_cont_{_}")
            
            latex_code = full_latex_code
            
            tex_path = os.path.join(PAPER_DIR, f"{safe_topic}_ResearchPaper.tex")
            if latex_code:
                 latex_code = latex_code.replace("```latex", "").replace("```", "").strip()
                 with open(tex_path, "w", encoding="utf-8") as f: f.write(latex_code)

            if os.path.exists(doc_path):
                 os.startfile(doc_path)
                 
                 conclusion = extract_conclusion(content)
                 msg = f"✅ Research Paper Generated! saved at {PAPER_DIR}"
                 if conclusion:
                     msg += f"\n\n🎓 **Conclusion Overview:**\n{conclusion}"
                 return msg
            else:
                 return "❌ Generated but failed to save file."

        except Exception as e:
            logger.error(f"Paper Error: {e}")
            return f"❌ Failed: {e}"
        finally:
            await browser.close()

async def wait_for_generation(page, step_name):
    """Helper to wait for generation to complete with extended timeout and 'Continue' support."""
    logger.info(f"Waiting for {step_name} generation...")
    
    # 1. Wait for 'Stop' button (Start) - Give it a second to appear
    await asyncio.sleep(2)

    # 2. Wait for Stability
    previous_len = 0
    stable_count = 0
    
    # Increase wait time: 1000 * 3s = 3000s (~50 minutes). 
    # Deep Research/Reasoning models can take a long time to "think" or write huge docs.
    MAX_RETRIES = 1000
    
    for i in range(MAX_RETRIES): 
        await asyncio.sleep(3)
        
        # --- Check for "Continue" button ---
        # DeepSeek sometimes pauses and shows a continue button for long outputs.
        # Logic: If we see a button that says "Continue generation", click it.
        try:
             # Look for typical "Continue" button. 
             # Selector might need adjustment based on exact UI, but text usually works.
             continue_btn = page.locator('div:has-text("Continue generation")').last
             if await continue_btn.count() > 0 and await continue_btn.is_visible():
                 logger.info(f"[{step_name}] Found 'Continue' button. Clicking...")
                 await continue_btn.click()
                 stable_count = 0 # Reset stability as we expect more text
                 await asyncio.sleep(2)
                 continue
        except Exception:
            pass
        
        # --- Check Content Length ---
        elements = await page.query_selector_all('.ds-markdown')
        if not elements:
            elements = await page.query_selector_all('div[class*="markdown"]')
        
        current_len = 0
        if elements:
            try:
                # Get the last message's content
                current_text = await elements[-1].inner_text()
                current_len = len(current_text)
            except:
                pass # Element might have detached
        
        logger.info(f"[{step_name}] Check {i}/{MAX_RETRIES}: {current_len} chars")

        if current_len > 100 and current_len == previous_len:
            stable_count += 1
            # Require 30 seconds of silence (10 checks) to confirm it is actually done
            # Improved from 5 to 10 for safety with "DeepThink" pauses.
            if stable_count >= 10:
                logger.info(f"[{step_name}] Generation complete (Stable for 30s).")
                break
        else:
            stable_count = 0
        
        previous_len = current_len
    
    # Screeny after each step
    try:
        await page.screenshot(path=os.path.join(DATA_DIR, f"debug_{step_name}_done.png"))
    except:
        pass

def extract_conclusion(text: str) -> str:
    """
    Extracts the conclusion section from a markdown report/paper.
    """
    try:
        # Regex to find "Conclusion" header (##, ###, or **)
        # We look for "Conclusion" followed by text until the next Header or End of String
        import re
        match = re.search(r"(?:^|\n)(?:#+\s*|\*+\s*)Conclusion(?:s)?.*?\n(.*?)(?:(?:\n#+ )|$)", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()[:1000] # Limit to 1000 chars for speaking
        return ""
    except:
        return ""

@function_tool
async def ask_deepseek(query: str) -> str:
    """
    Asks DeepSeek a question and returns the raw text response.
    Use this when the user wants a direct answer, explanation, or chat response 
    rather than a downloadable file/report.
    
    Args:
        query: The question or instruction to send to DeepSeek.
    """
    logger.info(f"Asking DeepSeek: {query}")
    
    async with async_playwright() as p:
        # --- Secure Browser Launch ---
        user_data_dir = os.path.join(DATA_DIR, "DeepSeekSession")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

        clean_browser_user_data(user_data_dir)

        try:
            logger.info("Launching Chrome with persistent context...")
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
        except:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        try:
            # 1. Navigate to Chat (Skip Login if possible)
            logger.info("Navigating to DeepSeek...")
            await page.goto("https://chat.deepseek.com/")
            
            # Check if login is needed (URL redirect OR visible login elements)
            # Give it a moment to settle
            await asyncio.sleep(3.0)
            
            # Case A: We are on the landing page but need to click "Log in"
            login_btn = page.locator('div[role="button"]:has-text("Log in"), button:has-text("Log in")').first
            if await login_btn.count() > 0 and await login_btn.is_visible():
                 logger.info("Found 'Log in' button. Clicking...")
                 await login_btn.click()
                 await asyncio.sleep(2.0)

            # Case B: We are on a login page
            if "login" in page.url or await page.locator('input[type="password"]').count() > 0:
                logger.info("Login required. Attempting auto-login...")
                try:
                     # 1. Fill Email
                     email_input = page.locator('input[type="text"], input[type="email"], input[placeholder*="Email"]').first
                     if await email_input.count() > 0:
                         logger.info(f"Filling email: {DS_EMAIL[:3]}***")
                         await email_input.fill(DS_EMAIL)
                     
                     # 2. Fill Password
                     pass_input = page.locator('input[type="password"]').first
                     if await pass_input.count() > 0:
                         logger.info("Filling password...")
                         await pass_input.fill(DS_PASS)
                     
                     # 3. Click Log In
                     submit_btn = page.locator('button[type="submit"], button:has-text("Log in"), div[role="button"]:has-text("Log in")').last
                     if await submit_btn.count() > 0:
                         logger.info("Clicking Submit/Login...")
                         await submit_btn.click()
                     
                     # Wait for redirect
                     await page.wait_for_url("https://chat.deepseek.com/**", timeout=10000) # Short wait for auto-login
                     logger.info("Login submitted. Waiting for chat...")

                except Exception as e:
                    logger.warning(f"Auto-login skipped or failed: {e}")
            
            # --- MANUAL LOGIN FALLBACK ---
            # If we are still not at the chat (no textarea), wait specifically for user to help
            try:
                await page.wait_for_selector('textarea', timeout=5000)
            except:
                logger.warning("Chat interface not found yet. YOU MAY NEED TO LOG IN MANUALLY.")
                # Wait up to 120 seconds for the user to solve captcha/login
                logger.info("Waiting 120s for manual login...")
                try:
                    await page.wait_for_selector('textarea', timeout=120000)
                    logger.info("Manual login detected! Proceeding...")
                except:
                    raise Exception("Timed out waiting for login/chat interface.")

            # 2. Enable Features
            # Try to find DeepThink button
            btn_deepthink = page.locator('.ds-toggle-button').filter(has_text="DeepThink")
            if await btn_deepthink.count() > 0:
                 classes = await btn_deepthink.get_attribute('class')
                 if 'ds-toggle-button--selected' not in classes:
                     await btn_deepthink.click()
            
            # 3. Send Query
            await page.fill('textarea', query)
            await page.keyboard.press('Enter')
            
            # 4. Wait for generation
            await wait_for_generation(page, "ask_deepseek")
            
            # 5. Scrape Full Response
            content = ""
            elements = await page.query_selector_all('.ds-markdown')
            if not elements:
                 elements = await page.query_selector_all('div[class*="markdown"]')
            
            if elements:
                # Get the last/newest response
                content = await elements[-1].inner_text()
            
            if not content:
                 # Fallback
                 frames = await page.query_selector_all('.ds-chat-item') 
                 if frames: content = await frames[-1].inner_text()

            if content:
                logger.info(f"Retrieved response ({len(content)} chars)")
                return content
            else:
                return "❌ DeepSeek replied, but I couldn't read the text."

        except Exception as e:
            logger.error(f"Ask DeepSeek Error: {e}")
            try:
                await page.screenshot(path=os.path.join(DATA_DIR, "error_screenshot.png"))
            except: pass
            return f"❌ Error asking DeepSeek: {e}"
        finally:
            await browser.close()

