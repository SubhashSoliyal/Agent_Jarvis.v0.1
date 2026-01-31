
import asyncio
import logging
from backend.Jarvis_storyteller import generate_story_and_audio
from dotenv import load_dotenv

# Load env for credentials
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    topic = "Two astronauts creating a black hole in their kitchen"
    characters = "Captain Nova and Dr. Quasar"
    print(f"--- SIMULATING USER COMMAND: 'Jarvis, make a story about {topic}' ---")
    
    result = await generate_story_and_audio(topic, characters)
    
    print("\n--- RESULT ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
