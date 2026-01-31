import asyncio
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

async def test_connect():
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    model_id = "gemini-2.0-flash-exp"
    
    configs = [
        {"response_modalities": ["AUDIO"]},
        {"response_modalities": ["AUDIO", "TEXT"]},
        None # Default
    ]
    
    for config in configs:
        print(f"\nTesting {model_id} with config: {config}...")
        try:
            async with client.aio.live.connect(model=model_id, config=config) as session:
                print("Connected successfully!")
                await session.send(input="Hello", end_of_turn=True)
                break
        except Exception as e:
            print(f"Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_connect())
