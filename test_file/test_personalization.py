import os
import sys
from dotenv import load_dotenv

# Ensure we can import from backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("--- Testing Personalization Integration ---")

try:
    from backend.Jarvis_prompts import personal_context, behavior_prompts
    print("[OK] Successfully imported Jarvis_prompts")
    print(f"Personal Context Length: {len(personal_context)}")
    # print(f"Personal Context Preview:\n{personal_context.strip()}") # Avoiding potential encoding issues with user data
    
    if "User Name:" not in personal_context:
        print("[FAIL] Error: 'User Name' not found in personal_context.")
    else:
        print("[OK] personal_context contains User Name.")

except Exception as e:
    print(f"[FAIL] Failed to import Jarvis_prompts: {e}")
    sys.exit(1)

try:
    from backend.Jarvis_utils import get_user_details
    print("[OK] Successfully imported Jarvis_utils.get_user_details")
    
    import asyncio
    import inspect
    
    if not inspect.iscoroutinefunction(get_user_details):
        print("[FAIL] get_user_details is NOT an async function!")
    else:
        print("[OK] get_user_details is an async function.")
        
    # Run the async function
    details = asyncio.run(get_user_details())
    # print(f"Tool Output:\n{details.strip()}")
    
    if personal_context.strip() in details:
        print("[OK] Tool output contains personal_context.")
    else:
        print("[FAIL] Tool output does not match personal_context.")
        
except Exception as e:
    print(f"[FAIL] Failed to import/run get_user_details: {e}")
    sys.exit(1)

print("\n--- Testing Agent Imports ---")
try:
    from agent import Assistant
    print("[OK] Successfully imported Assistant from agent.py (No circular imports detected)")
except ImportError as e:
    print(f"[FAIL] Failed to import Assistant: {e}")
except Exception as e:
    print(f"[FAIL] Error during agent import: {e}")

print("\n[OK] Verification Complete!")
