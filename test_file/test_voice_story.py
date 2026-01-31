
import asyncio
import logging
from backend.Jarvis_storyteller import generate_story_and_audio
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

async def main():
    topic = "An ancient robot waking up"
    characters = "Unit 1 and The Explorer"
    voice = "Puck" 
    
    print(f"--- SIMULATING USER COMMAND with Voice: {voice} ---")
    result = await generate_story_and_audio(topic, characters, voice_name=voice)
    print("\n--- RESULT ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
