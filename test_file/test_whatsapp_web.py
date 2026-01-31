import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("--- Testing WhatsApp Web Integration Code ---")

try:
    from backend.Jarvis_whatsapp import WhatsAppBrowser, send_whatsapp_message, USER_DATA_DIR
    print("[OK] Imported WhatsAppBrowser and tools.")
    print(f"[INFO] Profile Path: {USER_DATA_DIR}")
    
    if not os.path.exists(USER_DATA_DIR):
        print(f"[INFO] Profile directory does not exist yet (Expected for first run).")
    else:
        print(f"[INFO] Profile directory exists.")
        
except ImportError as e:
    print(f"[FAIL] Import Error: {e}")
    sys.exit(1)

print("\n[OK] Code structure verified. Run the agent to launch the browser.")
print("Reminder: First run requires manual QR Code scanning.")
