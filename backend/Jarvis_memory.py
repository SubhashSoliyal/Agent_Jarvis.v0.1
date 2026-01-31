import os
import logging
from mem0 import AsyncMemoryClient
from dotenv import load_dotenv
from livekit.agents import function_tool

load_dotenv()

logger = logging.getLogger("jarvis_memory")
logger.setLevel(logging.INFO)

class MemoryManager:
    def __init__(self):
        self.api_key = os.getenv("MEM0_API_KEY")
        if not self.api_key:
            logger.error("MEM0_API_KEY not found in environment variables.")
            self.memory = None
            return

        try:
            self.memory = AsyncMemoryClient(api_key=self.api_key)
            logger.info("AsyncMemoryClient initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize AsyncMemoryClient: {e}")
            self.memory = None

    async def add_memory(self, content: str):
        if not self.memory:
            return "Memory not initialized."
        try:
            user_id = os.getenv("USER_NAME", "Subhash")
            await self.memory.add(content, user_id=user_id)
            return "Memory added successfully."
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return f"Failed to add memory: {e}"

    async def retrieve_memory(self, query: str):
        if not self.memory:
            return "Memory not initialized."
        try:
            user_id = os.getenv("USER_NAME", "Subhash")
            results = await self.memory.search(query, filters={"user_id": user_id})
            # Format results into a readable string
            if not results or "results" not in results:
                return "No relevant memories found."
            
            memories = results["results"]
            if not memories:
                 return "No relevant memories found."

            formatted = "Relevant Memories:\n"
            for mem in memories:
                text = mem.get("memory", "")
                formatted += f"- {text}\n"
            return formatted
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return f"Failed to retrieve memory: {e}"

# Singleton instance
memory_manager = MemoryManager()

@function_tool
async def remember(detail: str) -> str:
    """
    Save a specific detail, fact, or preference to long-term memory. 
    Use this when the user asks you to remember something or provides important information.
    """
    logger.info(f"Remembering: {detail}")
    return await memory_manager.add_memory(detail)

@function_tool
async def recall(query: str) -> str:
    """
    Search long-term memory for information. 
    Use this when you need to recall past interactions, user preferences, or specific facts.
    """
    logger.info(f"Recalling: {query}")
    return await memory_manager.retrieve_memory(query)
