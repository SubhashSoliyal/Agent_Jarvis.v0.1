import aiohttp
import logging
from bs4 import BeautifulSoup
from livekit.agents import function_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs for Hindi Bulletins
NEWS_URLS = {
    "morning": "https://www.newsonair.gov.in/bulletins-detail-category/morning-news-hi/",
    "midday": "https://www.newsonair.gov.in/bulletins-detail-category/midday-news-hi/",
    "evening": "https://www.newsonair.gov.in/bulletins-detail-category/evening-news-hi/"
}

async def fetch_category_page(url: str) -> str:
    """Fetches the category page logic."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                logger.error(f"Failed to fetch news page: {response.status}")
                return ""
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return ""

@function_tool
async def get_news_bulletin(time_slot: str) -> str:
    """
    Fetches the latest Hindi news bulletin text for a specific time slot.
    args:
        time_slot: "morning", "midday" (or "afternoon"), or "evening".
    """
    slot = time_slot.lower().strip()
    if "afternoon" in slot:
        slot = "midday"
    
    url = NEWS_URLS.get(slot)
    if not url:
        return "❌ Invalid time slot. Please ask for Morning, Midday, or Evening news."

    logger.info(f"Fetching news for {slot} from {url}")
    html = await fetch_category_page(url)
    
    if not html:
        return f"❌ Could not fetch news for {slot}."

    # Parse HTML
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Inspection showed bullet points often in a 'wp-block-group' or similar list
        # We need to find the main list of news. 
        # Strategy: Look for the first <ul> or <ol> inside the main content area, 
        # or paragraphs <p> that look like news.
        
        # Let's try finding the main post content container.
        # Often WP has 'entry-content' or similar.
        
        # Since I cannot inspect interactively in this step, I'll try a generic content extraction 
        # targeting list items which usually hold the headlines in these bulletins.
        
        news_items = []
        
        # Try finding standard list items first, as they often list headlines
        # Searching for specific WP blocks or just generic <li> with substantial text
        for li in soup.find_all('li'):
            text = li.get_text().strip()
            if len(text) > 20: # Filter out navigation links
                news_items.append(text)
                if len(news_items) >= 10: # Limit to top 10 headlines
                    break
        
        # If no list items, try paragraphs
        if len(news_items) < 3:
             for p in soup.find_all('p'):
                text = p.get_text().strip()
                if len(text) > 40: # Filter short lines
                    news_items.append(text)
                    if len(news_items) >= 10:
                        break
        
        if not news_items:
            return "⚠ No news text found on the page. Use 'google_search' instead."

        formatted_news = f"📰 **{slot.capitalize()} News Bulletin**:\n\n"
        formatted_news += "\n".join([f"- {item}" for item in news_items])
        
        return formatted_news

    except Exception as e:
        logger.error(f"Parsing Error: {e}")
        return f"❌ Error parsing news content: {e}"
