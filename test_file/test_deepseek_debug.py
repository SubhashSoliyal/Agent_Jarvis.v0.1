import asyncio
import os
import sys

# Add current directory to path so we can import backend
sys.path.append(os.getcwd())

from backend.Jarvis_reporter import generate_deepseek_content

async def main():
    print("Testing generate_deepseek_content...")
    try:
        topic = "Explain Quantum Computing in 2 sentences"
        result = await generate_deepseek_content(topic=topic, content_type="Short Explanation")
        print("\n--- RESULT ---")
        print(result)
        print("----------------")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
