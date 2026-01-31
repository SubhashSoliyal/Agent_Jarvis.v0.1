
import asyncio
import logging
from backend.Jarvis_window_CTRL import play_on_youtube
# Monkey patch perform_google_search to return empty to test fallback
import backend.Jarvis_window_CTRL

async def mock_search(query, num=1):
    print("Mock search returning empty list...")
    return []

backend.Jarvis_window_CTRL.perform_google_search = mock_search

logging.basicConfig(level=logging.INFO)

async def test_fallback():
    print("Testing play_on_youtube fallback logic...")
    topic = "Rick Roll"
    result = await play_on_youtube(topic)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_fallback())
