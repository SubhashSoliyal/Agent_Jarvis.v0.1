import asyncio
import sys
import os
from unittest.mock import MagicMock

# Mock libraries not available or unsafe to run in test env
sys.modules["pyautogui"] = MagicMock()
sys.modules["win32gui"] = MagicMock()
sys.modules["win32con"] = MagicMock()
sys.modules["pygetwindow"] = MagicMock()
sys.modules["fuzzywuzzy"] = MagicMock()
sys.modules["fuzzywuzzy.process"] = MagicMock()

# Mock os.startfile to capture output
original_startfile = os.startfile if hasattr(os, 'startfile') else None
mock_startfile = MagicMock()
if hasattr(os, 'startfile'):
    os.startfile = mock_startfile
else:
    # If not on windows (likely not in this env?), we mock subprocess
    pass 

# Add path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.Jarvis_window_CTRL import play_on_spotify
import pyautogui

async def run_test():
    print("--- Testing Spotify Logic ---")
    song = "shape of you"
    print(f"Testing song: '{song}'")
    
    # Run function
    res = await play_on_spotify(song)
    print(f"Result: {res}")
    
    # Verify URI
    expected_query = "shape of you type:track"
    # URL encoded: shape%20of%20you%20type%3Atrack
    # The URI should be spotify:search:shape%20of%20you%20type%3Atrack
    
    calls = mock_startfile.call_args_list
    if calls:
        uri_called = calls[0][0][0]
        print(f"URI Called: {uri_called}")
        if "type%3Atrack" in uri_called or "type:track" in uri_called: # depends on quote implementation
             print("✅ URI contains 'type:track' filter.")
        else:
             print("❌ URI missing 'type:track' filter.")
    else:
        print("⚠ os.startfile was not called (Are we on Windows?)")

    # Verify Logic/Keys
    # Expected: Tab then Enter
    # Pyautogui mocks
    print("PyAutoGUI Calls:")
    for call in pyautogui.press.call_args_list:
        print(f"  - press({call[0][0]})")
        
    # Check sequence roughly
    pressed_keys = [call[0][0] for call in pyautogui.press.call_args_list]
    if "tab" in pressed_keys and "enter" in pressed_keys:
        print("✅ Key sequence (Tab -> Enter) detected.")
    else:
        print("❌ Key sequence verification failed.")

if __name__ == "__main__":
    asyncio.run(run_test())
