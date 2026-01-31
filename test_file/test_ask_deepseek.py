import asyncio
import os
import sys

# Add current directory to path so we can import backend
sys.path.append(os.getcwd())

from backend.Jarvis_reporter import ask_deepseek

async def main():
    print("Testing ask_deepseek...")
    try:
        query = "What is the primary function of mitochondria? Explain in one short sentence."
        print(f"Query: {query}")
        result = await ask_deepseek(query=query)
        print("\n--- RESULT ---")
        print(result)
        print("----------------")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
