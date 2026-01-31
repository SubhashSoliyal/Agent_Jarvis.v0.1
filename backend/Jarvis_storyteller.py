
import os
import logging
import asyncio
from livekit.agents import function_tool
from playwright.async_api import async_playwright
from backend.Jarvis_content_creator import _call_nvidia_llm
from backend.Jarvis_utils import clean_browser_user_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory to save stories and audio
DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")
STORY_DIR = os.path.join(DATA_DIR, "Stories")
if not os.path.exists(STORY_DIR):
    os.makedirs(STORY_DIR)

@function_tool
async def generate_story_and_audio(topic: str, characters: str, setting: str = "", voice_name: str = "Puck") -> str:
    """
    Generates a conversational story script and then creates an audio performance of it using the Google AI Studio limit-access TTS model.
    The tool will attempt to use browser automation to generate speech.
    
    Args:
        topic: The main subject or plot of the story.
        characters: A list or description of the characters involved (e.g. "Alice and Bob").
        setting: (Optional) Where the story takes place.
        voice_name: The name of the voice to use (e.g., "Puck", "Charon", "Aoede", "Kore", "Fenrir"). Defaults to "Puck".
    """
    logger.info(f"Generating story on {topic} with {characters} using voice {voice_name}...")
    
    # 1. Generate Script
    prompt = f"Write a short conversational story script between {characters} about {topic}. {setting} \n\nThe script should be dialogue-heavy. Format it clearly. Do not use asterisks for actions if possible, focus on spoken text."
    messages = [{"role": "user", "content": prompt}]
    
    try:
        story_script = _call_nvidia_llm(messages)
    except Exception as e:
        return f"❌ Failed to generate story script: {e}"

    # Save Script
    safe_topic = topic.replace(" ", "_").replace("/", "-")[:50]
    script_filename = f"{safe_topic}_script.txt"
    script_path = os.path.join(STORY_DIR, script_filename)
    
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(story_script)
        
    logger.info(f"Script saved to {script_path}. Now performing TTS with voice {voice_name}...")
    
    audio_path = await generate_audio_via_playwright(story_script, safe_topic, voice_name)
    
    if audio_path and os.path.exists(audio_path):
        return f"✅ Story generated and audio created!\nScript: {script_filename}\nVoice: {voice_name}\nAudio: {os.path.basename(audio_path)}\n\nYou can ask me to play '{os.path.basename(audio_path)}'."
    else:
        return f"⚠ Story generated but audio failed.\nScript saved at: {script_filename}\nError details: {audio_path if audio_path else 'Unknown error'}"

async def generate_audio_via_playwright(text: str, filename_base: str, voice_name: str) -> str:
    """
    Uses Playwright to interact with Google AI Studio and generate speech.
    Returns the path to the saved audio file or None/Error string.
    """
    url = "https://aistudio.google.com/live" # The user said "generate-speech?model=gemini-2.5-pro-preview-tts" which redirects or is specific.
    # Actually wait, the user provided a very specific URL: https://aistudio.google.com/generate-speech?model=gemini-2.5-pro-preview-tts
    specific_url = "https://aistudio.google.com/generate-speech?model=gemini-2.5-pro-preview-tts"
    
    async with async_playwright() as p:
        # Path for persistent user data (cookies, login session)
        user_data_dir = os.path.join(DATA_DIR, "ChromeSession")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

        # Clean up lock files before launch
        clean_browser_user_data(user_data_dir)

        # Use launch_persistent_context to keep login session and use actual Chrome
        try:
            logger.info("Launching Chrome with persistent context...")
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome", # Use installed Chrome
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"] # Hide automation
            )
        except Exception as e:
            logger.warning(f"Could not launch Chrome channel ({e}). Falling back to bundled Chromium.")
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        try:
            logger.info(f"Navigating to {specific_url}...")
            await page.goto(specific_url)
            
            # Wait for user login if redirected
            # We'll check for a key element of the logged-in specialized page.
            # Assuming there's a specific input box.
            
            # Since I don't know the exact DOM of this beta page, I'll prompt user interaction or basic wait.
            # But the user asked for a tool. A tool should be automated.
            # Best effort: Wait for a textarea and fill it.
            
            # Wait up to 120s for the page to be ready (including user manual login if needed first time)
            # Check if we are on login page
            if "accounts.google.com" in page.url:
                logger.info("Detected login page. Attempting auto-login...")
                try:
                    email = os.getenv("GOOGLE_EMAIL")
                    password = os.getenv("GOOGLE_PASSWORD")
                    
                    if email and password:
                        # Email
                        logger.info("Entering email...")
                        await page.fill('input[type="email"]', email)
                        await page.click('#identifierNext')
                        
                        # Wait for password field
                        await page.wait_for_selector('input[type="password"]', state="visible", timeout=10000)
                        logger.info("Entering password...")
                        await page.fill('input[type="password"]', password)
                        await page.click('#passwordNext')
                        
                        logger.info("Login submitted. Waiting for redirection...")
                        await page.wait_for_url("https://aistudio.google.com/**", timeout=60000)
                    else:
                        logger.warning("Google credentials not found in env. Waiting for manual login...")
                except Exception as e:
                    logger.error(f"Auto-login failed: {e}. Please log in manually.")

            # --- Ensure Single-Speaker Mode ---
            try:
                # Try to find the text "Single-speaker audio" anywhere and click it
                # Using a broad text matching because roles can be finicky
                single_mode_text = page.get_by_text("Single-speaker audio").first
                if await single_mode_text.count() > 0:
                     logger.info("Found 'Single-speaker audio' text. Clicking...")
                     await single_mode_text.click()
                     await asyncio.sleep(2.0)
                else:
                     logger.warning("'Single-speaker audio' text not found.")
            except Exception as e:
                logger.warning(f"Failed to switch to Single-speaker mode: {e}")

            except Exception as e:
                logger.warning(f"Failed to switch to Single-speaker mode: {e}")

            # Correctly identify the main text input.
            # TEXTAREA 0 is typically "Style instructions". We want the one for content.
            textarea = page.get_by_placeholder("Start writing or paste text here to generate speech").first
            if await textarea.count() == 0:
                 # Fallback if placeholder changes
                 textareas = page.locator("textarea")
                 if await textareas.count() > 1:
                     textarea = textareas.nth(1) # Likely the second one
                 else:
                     textarea = textareas.first

            try:
                await textarea.wait_for(timeout=30000)
            except:
                # Retry finding textarea
                textarea = page.locator("textarea").nth(1)
                await textarea.wait_for(timeout=60000)
            
            # --- Voice Selection ---
            try:
                logger.info(f"Attempting to select voice: {voice_name}")
                
                # WAIT for any voice selector to appear. 
                # We look for the standard listbox or a button that looks like a voice selector.
                # This prevents the 18ms fail.
                try:
                    # Generic wait for a listbox or a settings button
                    await page.wait_for_selector("div[role='listbox'], button[aria-haspopup='listbox']", timeout=5000)
                except:
                    pass # Proceed to heuristics

                # 1. Try standard listbox
                voice_dropdown = page.get_by_role("listbox").first
                
                # 2. Heuristic: Button with known voice name 
                if await voice_dropdown.count() == 0:
                     common_voices = ["Puck", "Charon", "Aoede", "Kore", "Fenrir", "Orus"]
                     for v in common_voices:
                         if await page.get_by_text(v, exact=True).count() > 0:
                             # Found a voice name text. Is it clickable?
                             # Let's try locating the button containing it
                             possible_btn = page.locator(f"button:has-text('{v}')").first
                             if await possible_btn.count() > 0:
                                 voice_dropdown = possible_btn
                                 break
                
                if await voice_dropdown.count() > 0:
                    current_voice = await voice_dropdown.inner_text()
                    if voice_name.lower() not in current_voice.lower():
                        await voice_dropdown.click()
                        await asyncio.sleep(1.0)
                        
                        # Select Option
                        voice_option = page.get_by_text(voice_name, exact=True).first
                        if await voice_option.count() == 0:
                             voice_option = page.get_by_text(voice_name).first
                        
                        if await voice_option.count() > 0:
                            await voice_option.click()
                            logger.info(f"Selected voice: {voice_name}")
                            await asyncio.sleep(1.0) 
                        else:
                            logger.warning(f"Voice option '{voice_name}' not found. Using default.")
                            await page.keyboard.press("Escape")
                    else:
                        logger.info(f"Voice is already set to {voice_name}")
                else:
                    logger.warning("Voice dropdown not found. Skipping selection.")
            except Exception as e:
                logger.warning(f"Voice selection failed: {e}")

            await textarea.fill(text[:4000]) # Safety limit
            
            # Find Generate button
            # We identified it has aria-label="Run" and text "RunCtrlkeyboard_return"
            button_clicked = False
            
            # 0. Check if Settings Panel is open and close it
            close_settings = page.locator("button[aria-label='Close run settings panel']").first
            if await close_settings.count() > 0 and await close_settings.is_visible():
                logger.info("Settings panel detected. Closing...")
                await close_settings.click()
                await asyncio.sleep(0.5)

            # Trigger Generation
            # NUCLEAR OPTION: Direct JS interaction
            # 1. Dispatch input event to ensure Angular picks up the text
            logger.info("Dispatching input event to sync text...")
            await textarea.evaluate("el => { el.dispatchEvent(new Event('input', {bubbles: true})); el.dispatchEvent(new Event('change', {bubbles: true})); }")
            await asyncio.sleep(0.5)

            button_clicked = False
            
            # 2. Try clicking Run button via JS (bypasses overlays/visibility checks)
            run_btn = page.locator("button[aria-label='Run']").first
            if await run_btn.count() == 0:
                 run_btn = page.locator("button[aria-label='Generate']").first
            
            if await run_btn.count() > 0:
                 logger.info("Clicking Run button via JS...")
                 await run_btn.evaluate("el => el.click()")
                 button_clicked = True
            else:
                 # Fallback to shortcut if button not found (unlikely)
                 logger.info("Run button not found for JS click. Using Ctrl+Enter...")
                 await textarea.focus()
                 await page.keyboard.press("Control+Enter")
                 button_clicked = True

            # Verify if generation started
            try:
                await asyncio.sleep(2.0)
                if await page.locator("button[aria-label='Stop']").count() > 0:
                     logger.info("Generation started (Stop button appeared).")
            except:
                pass 
            
            logger.info("Waiting for audio download button...")
            
            # --- Wait for Generation to Complete ---
            # This can take 10-30 seconds.
            # We look for the "Download" button to appear.
            
            download_btn = None
            try:
                # 1. Try standard text or aria-label
                # Wait for any of these to be visible
                await page.wait_for_selector("button[aria-label='Download'], button[aria-label='Download audio'], button:has-text('Download')", timeout=120000)
                
                # Identify which one appeared
                if await page.locator("button[aria-label='Download']").count() > 0:
                     download_btn = page.locator("button[aria-label='Download']").first
                elif await page.locator("button[aria-label='Download audio']").count() > 0:
                     download_btn = page.locator("button[aria-label='Download audio']").first
                elif await page.locator("button", has_text="Download").count() > 0:
                     download_btn = page.locator("button", has_text="Download").first
                else: 
                     # Should rarely happen if wait_for_selector passed, but good fallback
                     # Try finding an icon button (e.g. material icon 'download')
                     download_btn = page.locator("button span.material-icons:has-text('download')").locator("..").first
                
            except Exception as e:
                 logger.warning(f"Download button wait timed out: {e}")
                 # Last ditch: check if there's a file link?
                 await page.screenshot(path=os.path.join(STORY_DIR, "debug_gen_fail.png"))
                 with open(os.path.join(STORY_DIR, "debug_dump.html"), "w", encoding="utf-8") as f:
                     f.write(await page.content())
                 return "❌ Timed out waiting for audio generation (Download button did not appear). HTML dump saved."

            if download_btn and await download_btn.count() > 0:
                logger.info("Download button found. Clicking...")
                async with page.expect_download(timeout=60000) as download_info:
                    # Sometimes you need to hover or focus
                    await download_btn.hover()
                    await download_btn.click()
                
                download = await download_info.value
                save_path = os.path.join(STORY_DIR, f"{filename_base}.wav")
                await download.save_as(save_path)
                
                logger.info(f"Saved audio: {save_path}")
                await browser.close()
                return save_path
            else:
                 return "❌ Download button selector failed after wait."

            async with page.expect_download(timeout=60000) as download_info:
                await download_btn.click()
                
            download = await download_info.value
            save_path = os.path.join(STORY_DIR, f"{filename_base}.wav")
            await download.save_as(save_path)
            
            logger.info(f"Saved audio: {save_path}")
            await browser.close()
            return save_path

        except Exception as e:
            try:
                await page.screenshot(path=os.path.join(STORY_DIR, "debug_error.png"))
            except:
                pass
            await browser.close()
            logger.error(f"Playwright automation failed: {e}")
            return f"❌ Automation Error: {e}"

