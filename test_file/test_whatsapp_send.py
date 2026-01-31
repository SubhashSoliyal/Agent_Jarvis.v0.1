import asyncio
import os
import sys

# Add path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.Jarvis_whatsapp import send_whatsapp_message, WhatsAppBrowser

async def main():
    print("--- Testing WhatsApp Send ---")
    contact = "ruchi mtech"
    message = "Hello, this is a test message from Jarvis AI validation system."
    
    print(f"Target: {contact}")
    print(f"Message: {message}")
    print("Launching browser... (Please scan QR code if asked)")
    
    result = await send_whatsapp_message(contact, message)
    print(f"Result: {result}")
    
    # Keep browser open briefly to see the result
    await asyncio.sleep(5)
    
    # Close explicitly
    await WhatsAppBrowser.close()
    print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())
