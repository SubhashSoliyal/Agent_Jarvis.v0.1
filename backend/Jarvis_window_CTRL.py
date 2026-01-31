import os
import subprocess
import logging
import sys
import asyncio
import aiohttp
import shutil
from fuzzywuzzy import process
import pyautogui

try:
    from livekit.agents import function_tool
except ImportError:
    def function_tool(func): 
        return func

from backend.Jarvis_google_search import perform_google_search

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

# Setup encoding and logger
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dynamic App Paths
start_menu_programs = os.path.join(os.environ['PROGRAMDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')
user_start_menu = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')

def find_app_path(app_name):
    """Helper to try and find an app's executable."""
    # Check common locations
    common_paths = [
        shutil.which(app_name),
        os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Google\\Chrome\\Application\\chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Google\\Chrome\\Application\\chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs\\Microsoft VS Code\\Code.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Postman\\Postman.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "VideoLAN\\VLC\\vlc.exe"),
        os.path.join(os.environ.get("APPDATA", ""), "Spotify\\Spotify.exe")
    ]
    
    for path in common_paths:
        if path and os.path.exists(path) and app_name.lower() in path.lower():
            return path
            
    return app_name # Return name to let system try to find it in PATH

# Adjusted Mappings
APP_MAPPINGS = {
    "notepad": "notepad",
    "calculator": "calc",
    "command prompt": "cmd",
    "control panel": "control",
    "settings": "start ms-settings:",
    "paint": "mspaint",
    "chrome": find_app_path("chrome.exe") or "chrome",
    "vlc": find_app_path("vlc.exe") or "vlc",
    "vs code": find_app_path("Code.exe") or "code",
    "postman": find_app_path("Postman.exe") or "postman",
    "youtube": "https://www.youtube.com",
    "spotify": find_app_path("Spotify.exe") or "spotify",
    "whatsapp": "whatsapp:",
    "whatsapp web": "https://web.whatsapp.com",
    "camera": "microsoft.windows.camera:",
    "photos": "microsoft.windows.photos:",
    "calendar": "outlookcal:",
    "clock": "ms-clock:",
    "calculator": "calc"
}

def scan_start_menu_links():
    """Scans Start Menu for .lnk files to find apps."""
    apps = {}
    paths = [
        os.path.join(os.environ['PROGRAMDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
        os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')
    ]
    for p in paths:
        if not os.path.exists(p): continue
        for root, dirs, files in os.walk(p):
            for file in files:
                if file.endswith(".lnk"):
                    name = file.replace(".lnk", "").lower()
                    full_path = os.path.join(root, file)
                    apps[name] = full_path
    return apps

# -------------------------
# Global focus utility
# -------------------------
async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow")
        return False

    await asyncio.sleep(1.5)  # Give time for window to appear
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            return True
    return False

# Index files/folders
async def index_items(base_dirs):
    item_index = []
    # Filter non-existent directories to avoid errors
    valid_dirs = [d for d in base_dirs if os.path.exists(d)]
    
    for base_dir in valid_dirs:
        for root, dirs, files in os.walk(base_dir):
            for d in dirs:
                item_index.append({"name": d, "path": os.path.join(root, d), "type": "folder"})
            for f in files:
                item_index.append({"name": f, "path": os.path.join(root, f), "type": "file"})
    logger.info(f"✅ Indexed {len(item_index)} items.")
    return item_index

async def search_item(query, index, item_type):
    filtered = [item for item in index if item["type"] == item_type]
    choices = [item["name"] for item in filtered]
    if not choices:
        return None
    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 Matched '{query}' to '{best_match}' with score {score}")
    if score > 70:
        for item in filtered:
            if item["name"] == best_match:
                return item
    return None

# File/folder actions
async def open_folder(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ फ़ाइल open करने में error आया। {e}")

async def play_file(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ फ़ाइल open करने में error आया।: {e}")

async def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Folder create हो गया।: {path}"
    except Exception as e:
        return f"❌ फ़ाइल create करने में error आया।: {e}"

async def rename_item(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return f"✅ नाम बदलकर {new_path} कर दिया गया।"
    except Exception as e:
        return f"❌ नाम बदलना fail हो गया: {e}"

async def delete_item(path):
    try:
        # Safety check: don't delete system roots
        if len(path) < 4: 
            return "❌ Safety: Root paths delete नहीं कर सकते।"
            
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"🗑️ Deleted: {path}"
    except Exception as e:
        return f"❌ Delete नहीं हुआ।: {e}"

# App control
@function_tool
async def open_app(app_title: str) -> str:
    app_title = app_title.lower().strip()
    
    # 1. Try APP_MAPPINGS first (Hardcoded & Optimized)
    if app_title in APP_MAPPINGS:
        app_command = APP_MAPPINGS[app_title]
        cmd = f'start "" "{app_command}"' if " " in app_command and not app_command.startswith("start") else f'start {app_command}'
        if "ms-settings" in app_command or ":" in app_command and not "http" in app_command and not "C:" in app_command:
             # Handle UWP URIs like microsoft.windows.camera: or ms-settings: - they work best with direct start
             cmd = f'start {app_command}'
        
        try:
            await asyncio.create_subprocess_shell(cmd, shell=True)
            await focus_window(app_title) # Attempt focus
            return f"🚀 App launch initiated: {app_title}"
        except Exception as e:
            logger.error(f"Mapping launch failed: {e}")
            # Fallthrough to search if mapping fails? No, mapping failure usually means system issue.
            return f"❌ Failed to launch {app_title} from mapping: {e}"

    # 2. Smart Search in Start Menu
    logger.info(f"App not in mappings, scanning Start Menu for: {app_title}")
    start_menu_apps = scan_start_menu_links()
    
    # Exact match check first
    if app_title in start_menu_apps:
        target_path = start_menu_apps[app_title]
    else:
        # Fuzzy match
        choices = list(start_menu_apps.keys())
        if not choices:
             return f"❌ No apps found in Start Menu to match '{app_title}'."
             
        best_match, score = process.extractOne(app_title, choices)
        logger.info(f"Fuzzy match for app '{app_title}': '{best_match}' (Score: {score})")
        
        if score > 75:
            target_path = start_menu_apps[best_match]
        else:
            return f"❌ Could not find app '{app_title}'. Best guess was '{best_match}' ({score}%), which is too low."

    # Launch the found shortcut
    try:
        os.startfile(target_path)
        # Try to focus based on the matched name
        await asyncio.sleep(2) # Wait for launch
        await focus_window(os.path.basename(target_path).replace(".lnk", ""))
        return f"🚀 Launched from Start Menu: {os.path.basename(target_path).replace('.lnk', '')}"
    except Exception as e:
        return f"❌ Found app but failed to launch: {e}"


@function_tool
async def play_on_youtube(topic: str) -> str:
    """
    Plays a video or song on YouTube by searching for the topic and opening the first video result.
    Use this when the user asks to "play [song/video] on YouTube".
    """
    import re # Ensure re is imported for fallback logic

    topic = topic.strip()
    logger.info(f"Searching for YouTube video: {topic}")
    
    found_title = topic
    url = ""

    if topic.startswith("http://") or topic.startswith("https://"):
        url = topic
        found_title = "Direct URL"
        logger.info(f"Playing direct URL: {url}")
    else:
        # 1. Try Google Search API first (Fastest if available)
        try:
            results = await perform_google_search(f"site:youtube.com {topic}", num=1)
        except Exception as e:
            logger.warning(f"Google Search API failed for YouTube: {e}")
            results = []

        if results:
            first_result = results[0]
            link = first_result.get("link")
            title = first_result.get("title")
            if link and ("watch?v=" in link or "youtu.be/" in link):
                url = link
                if "?" in url:
                    url += "&autoplay=1"
                else:
                    url += "?autoplay=1"
                found_title = title
                logger.info(f"Found video via Google API: {title} - {url}")

        # 2. Fallback: Scrape YouTube Search Results (Robust if API fails)
        if not url:
            logger.info("Google API yielded no video. Attempting HTML scrape fallback...")
            try:
                search_url = f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            # Try to find videoId in initial data
                            # "videoId":"..."
                            match = re.search(r'"videoId":"(.*?)"', html)
                            if match:
                                video_id = match.group(1)
                                url = f"https://www.youtube.com/watch?v={video_id}"
                                found_title = f"{topic} (Scraped)"
                                logger.info(f"Found video via scrape: {url}")
                            else:
                                logger.warning("Regex failed to find videoId in YouTube HTML.")
                        else:
                            logger.warning(f"Failed to fetch YouTube search page: {response.status}")
            except Exception as e:
                logger.error(f"Scraping fallback failed: {e}")

        # 3. Final Fallback: Direct Search Page
        if not url:
            logger.info("All search methods failed. Opening search page.")
            url = f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}"
            found_title = "Search Results Page"

    try:
        # Open in default browser
        if os.name == 'nt':
            os.startfile(url)
        else:
            subprocess.call(['xdg-open', url])
            
        return f"✅ YouTube par play kar raha hoon: {found_title}"
    except Exception as e:
        return f"❌ YouTube open karne mein error: {e}"


@function_tool
async def play_on_spotify(topic: str) -> str:
    """
    Plays a song, playlist, or artist on Spotify by searching for the link and playing it directly.
    Use this when the user asks to "play [topic] on Spotify".
    """
    topic = topic.strip()
    logger.info(f"Searching for Spotify media: {topic}")
    
    spotify_uri = ""
    found_title = topic

    # 1. Search for direct link via Google (Reliable playback)
    # We look for 'open.spotify.com/...'
    try:
        results = await perform_google_search(f"site:open.spotify.com {topic}", num=1)
        if results:
            first = results[0]
            link = first.get("link")
            title = first.get("title")
            
            if link and "open.spotify.com/" in link:
                clean_link = link.split("?")[0]
                # Handle different types
                if "/track/" in clean_link:
                    entry_id = clean_link.split("/track/")[1]
                    spotify_uri = f"spotify:track:{entry_id}"
                elif "/playlist/" in clean_link:
                    entry_id = clean_link.split("/playlist/")[1]
                    spotify_uri = f"spotify:playlist:{entry_id}"
                elif "/album/" in clean_link:
                    entry_id = clean_link.split("/album/")[1]
                    spotify_uri = f"spotify:album:{entry_id}"
                elif "/artist/" in clean_link:
                    entry_id = clean_link.split("/artist/")[1]
                    spotify_uri = f"spotify:artist:{entry_id}"
                
                if spotify_uri:
                    found_title = title
                    logger.info(f"Found Spotify URI: {spotify_uri} ({title})")

    except Exception as e:
        logger.warning(f"Google Search for Spotify failed: {e}")

    # 2. Fallback to generic search if link not found
    if not spotify_uri:
        import urllib.parse
        encoded_query = urllib.parse.quote(topic)
        spotify_uri = f"spotify:search:{encoded_query}"
        logger.info(f"Media not found directly. Opening search: {spotify_uri}")

    try:
        # Open URI
        if os.name == 'nt':
            os.startfile(spotify_uri)
        else:
            subprocess.call(['xdg-open', spotify_uri])
            
        # Give it time to focus and load
        await asyncio.sleep(3.5) 
        
        # PLAYBACK TRIGGER LOGIC
        # If it's a direct track/playlist, we often need to nudge it to play.
        # If it's a search, we might want to play the Top Result.
        await focus_window("Spotify")
        pyautogui.press('enter') # Often starts playing the top result or selected track
        await asyncio.sleep(0.5)
        # Backup: If 'enter' didn't work (maybe focus issue), try space? No, space might pause if already playing. 
        # Let's stick to Enter.
        
        if "spotify:search:" not in spotify_uri:
             return f"✅ Spotify par play kar raha hoon: {found_title}"
        else:
             return f"✅ Spotify par search result play kiya: {topic}"

    except Exception as e:
        return f"❌ Spotify open karne mein error: {e}"

@function_tool
async def close(window_title: str) -> str:
    if not win32gui:
        return "❌ win32gui missing"

    window_title = window_title.lower().strip()
    
    # PROTECTED WINDOWS LIST
    # These windows should NEVER be closed by the agent
    protected_keywords = ["livekit", "playground", "jarvis", "agent", "visual studio code", "console"]
    
    for safe_word in protected_keywords:
        if safe_word in window_title:
             return f"🛡️ Safety Protocol: I cannot close '{window_title}' because it is part of my operating system."

    def enumHandler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            curr_title = win32gui.GetWindowText(hwnd).lower()
            if window_title in curr_title:
                # Double check actual window title before closing
                is_safe = True
                for safe_word in protected_keywords:
                    if safe_word in curr_title:
                        is_safe = False
                        break
                
                if is_safe:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    logger.info(f"Closed window: {curr_title}")
                else:
                    logger.warning(f"Prevented closing protected window: {curr_title}")

    win32gui.EnumWindows(enumHandler, None)
    return f"✅ Command executed to close: {window_title}"

# Jarvis command logic
@function_tool
async def folder_file(command: str) -> str:
    user_home = os.path.expanduser("~")
    # Scan standard directories properly
    folders_to_index = [
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "Downloads")
    ]
    
    index = await index_items(folders_to_index)
    command_lower = command.lower()

    if "create folder" in command_lower:
        folder_name = command.replace("create folder", "").strip()
        # Default to Documents if no context, or just user home
        path = os.path.join(os.path.join(user_home, "Documents"), folder_name)
        return await create_folder(path)

    if "rename" in command_lower:
        parts = command_lower.replace("rename", "").strip().split("to")
        if len(parts) == 2:
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            item = await search_item(old_name, index, "folder")
            if item:
                new_path = os.path.join(os.path.dirname(item["path"]), new_name)
                return await rename_item(item["path"], new_path)
        return "❌ rename command valid नहीं है।"

    if "delete" in command_lower:
        item = await search_item(command, index, "folder") or await search_item(command, index, "file")
        if item:
            return await delete_item(item["path"])
        return "❌ Delete करने के लिए item नहीं मिला।"

    if "folder" in command_lower or "open folder" in command_lower:
        item = await search_item(command, index, "folder")
        if item:
            await open_folder(item["path"])
            return f"✅ Folder opened: {item['name']}"
        return "❌ Folder नहीं मिला।."

    item = await search_item(command, index, "file")
    if item:
        await play_file(item["path"])
        return f"✅ File opened: {item['name']}"

    return "⚠ कुछ भी match नहीं हुआ।"
