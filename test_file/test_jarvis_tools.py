import asyncio
from dotenv import load_dotenv
import logging

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("JarvisTest")

# Import tools
try:
    from backend.Jarvis_google_search import google_search
    from backend.jarvis_get_whether import get_weather
    from backend.Jarvis_window_CTRL import folder_file
    print("✅ All modules imported successfully.\n")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

async def test_tools():
    print("--- 🧪 Testing Jarvis Tools 🧪 ---\n")

    # 1. Test Weather
    print("1️⃣  Testing Weather...")
    try:
        weather_report = await get_weather("Delhi")
        print(f"   Result:\n{weather_report}\n")
    except Exception as e:
        print(f"   ❌ Weather test failed: {e}\n")

    # 2. Test Google Search
    print("2️⃣  Testing Google Search...")
    try:
        search_result = await google_search("What is LiveKit?")
        # Print just the first few lines to keep it clean
        summary = "\n".join(search_result.splitlines()[:5])
        print(f"   Result (Snippet):\n{summary}...\n")
    except Exception as e:
        print(f"   ❌ Search test failed: {e}\n")

    # 3. Test File Operation (Create Folder)
    print("3️⃣  Testing File Operations (Create Folder)...")
    try:
        # We will try to create a folder named 'Jarvis_Test_Folder' in D:/ (as per script logic)
        # Note: The script logic hardcodes D:/ in some places, let's see how it behaves.
        # Ideally we'd validte this isn't destructive.
        
        # Checking folder_file implementation in previous turn: it looks at "create folder" command.
        result = await folder_file("create folder Jarvis_Test_Folder")
        print(f"   Result: {result}\n")
    except Exception as e:
        print(f"   ❌ File op test failed: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_tools())
