import asyncio
import logging
from backend.Jarvis_reporter import generate_deepseek_report

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

async def test():
    print("Starting DeepSeek Report Test...")
    try:
        result = await generate_deepseek_report("thermodynamics analysis of a gas in a closed container with a movable piston and formula")
        print(f"RESULT: {result}")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test())
