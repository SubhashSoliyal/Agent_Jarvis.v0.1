import asyncio
import logging
from backend.Jarvis_qwen import generate_qwen_content

logging.basicConfig(level=logging.INFO)

async def test():
    print("Testing Qwen Content Generation...")
    try:
        # Test Topic: Leave Application
        result = await generate_qwen_content("Leave Application for Cousin's Wedding", "Application")
        print(f"RESULT: {result}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test())
