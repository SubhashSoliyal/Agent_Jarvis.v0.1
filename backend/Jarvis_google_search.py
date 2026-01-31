import os
import aiohttp
import logging
from dotenv import load_dotenv
from livekit.agents import function_tool
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def perform_google_search(query: str, num: int = 10) -> list:
    """
    Performs a Google Custom Search and returns the raw items.
    """
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        logger.error("API key or Search Engine ID missing.")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": num
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Google API error: {response.status} - {text}")
                    return []

                data = await response.json()
                return data.get("items", [])

    except Exception as e:
        logger.exception(f"Google Search error: {e}")
        return []

@function_tool
async def google_search(query: str) -> str:
    logger.info(f"Query received: {query}")
    results = await perform_google_search(query, num=5)

    if not results:
        logger.info("No results found.")
        return "No results found."

    formatted = ""
    logger.info("Search results:")
    for i, item in enumerate(results, start=1):
        title = item.get("title", "No title")
        link = item.get("link", "No link")
        snippet = item.get("snippet", "")
        formatted += f"{i}. {title}\n{link}\n{snippet}\n\n"
        logger.info(f"{i}. {title}\n{link}\n{snippet}\n")

    return formatted.strip()

@function_tool
async def get_current_datetime() -> str:
    return datetime.now().isoformat()
