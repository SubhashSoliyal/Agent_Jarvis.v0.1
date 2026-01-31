
import asyncio
import os
import logging
from backend.Jarvis_reporter import generate_deepseek_report

# Setup logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("Testing generate_deepseek_report...")
    try:
        # Attempt to call it directly. If it's a tool, it might be callable.
        # If not, we'll try accessing .fn or similar in a catch block if possible, 
        # but for now let's just try calling the object.
        result = await generate_deepseek_report("Fluid Dynamics")
        print("RESULT:", result)
    except TypeError as e:
        print(f"Call failed: {e}")
        # If not callable, maybe it's an object with a method?
        # But looking at livekit code usually @function_tool preserves the function or makes it a Callable.
        # If it returns a FunctionTool object, we might need to find the underlying method.
        pass

if __name__ == "__main__":
    asyncio.run(main())
