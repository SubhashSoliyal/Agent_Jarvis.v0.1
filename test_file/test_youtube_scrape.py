
import aiohttp
import asyncio
import re

async def get_video_id(query):
    query = query.replace(" ", "+")
    url = f"https://www.youtube.com/results?search_query={query}"
    print(f"Fetching {url}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                # Regex for video ID
                # Look for "videoId":"..." which is present in the initial data JSON
                match = re.search(r'"videoId":"(.*?)"', html)
                if match:
                    return match.group(1)
                
                # Fallback simple regex for href="/watch?v=..."
                match = re.search(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
                if match:
                    return match.group(1)
            else:
                print(f"Failed to fetch content: {response.status}")
    return None

async def test():
    topic = "Rick Roll"
    vid = await get_video_id(topic)
    print(f"Found Video ID: {vid}")
    if vid:
        print(f"Link: https://www.youtube.com/watch?v={vid}")

if __name__ == "__main__":
    asyncio.run(test())
