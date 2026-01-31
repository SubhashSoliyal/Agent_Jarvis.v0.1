
import asyncio
import logging
from backend.Jarvis_window_CTRL import play_on_youtube

logging.basicConfig(level=logging.INFO)

async def test():
    print("Testing play_on_youtube...")
    topic = "Ed Sheeran Shape of You"
    result = await play_on_youtube(topic)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test())
