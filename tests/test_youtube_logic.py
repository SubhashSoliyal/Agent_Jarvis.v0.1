
import asyncio
import logging

# Mock logger
logging.basicConfig(level=logging.INFO)

async def test_youtube_logic_mock():
    print("Testing YouTube Logic...")
    
    # Mock search results
    mock_results_std = [{"link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Rick Roll"}]
    mock_results_short = [{"link": "https://youtu.be/dQw4w9WgXcQ", "title": "Rick Roll Short"}]
    mock_results_none = [{"link": "https://google.com", "title": "Random Site"}]
    
    # Logic simulation
    def process_results(results):
        if results:
            first_result = results[0]
            link = first_result.get("link")
            title = first_result.get("title")
            
            if link and ("watch?v=" in link or "youtu.be/" in link):
                url = link
                if "?" in url:
                    url += "&autoplay=1"
                else:
                    url += "?autoplay=1"
                return url, title
            else:
                return None, None
        return None, None

    # Test 1: Standard Link
    url, title = process_results(mock_results_std)
    assert "autoplay=1" in url
    assert "watch?v=" in url
    print(f"Test 1 Passed: {url}")

    # Test 2: Short Link
    url, title = process_results(mock_results_short)
    assert "autoplay=1" in url
    assert "youtu.be" in url
    print(f"Test 2 Passed: {url}")
    
    print("All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_youtube_logic_mock())
