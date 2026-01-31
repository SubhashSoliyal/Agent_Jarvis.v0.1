import os
import asyncio
import logging
from livekit.agents import function_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure Data directory exists
DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

TODO_FILE = os.path.join(DATA_DIR, "todo_list.txt")

@function_tool
async def add_todo(task: str) -> str:
    """
    Adds a new task to things to do list.
    """
    try:
        with open(TODO_FILE, "a") as f:
            f.write(f"{task}\n")
        return f"✅ Added to To-Do list: {task}"
    except Exception as e:
        return f"❌ Error adding to list: {e}"

@function_tool
async def get_todo_list() -> str:
    """
    Reads the current To-Do list.
    """
    try:
        if not os.path.exists(TODO_FILE):
            return "📝 Your To-Do list is empty."
        
        with open(TODO_FILE, "r") as f:
            lines = f.readlines()
        
        if not lines:
            return "📝 Your To-Do list is empty."
            
        formatted_list = "Here is your To-Do list:\n"
        for i, line in enumerate(lines, 1):
            formatted_list += f"{i}. {line.strip()}\n"
            
        return formatted_list
    except Exception as e:
        return f"❌ Error reading list: {e}"

@function_tool
async def delete_todo_item(item_number: int) -> str:
    """
    Deletes an item from the To-Do list by its number (1-based index).
    """
    try:
        if not os.path.exists(TODO_FILE):
            return "❌ List is empty, nothing to delete."
            
        with open(TODO_FILE, "r") as f:
            lines = f.readlines()
            
        if item_number < 1 or item_number > len(lines):
            return f"❌ Invalid item number. Please choose between 1 and {len(lines)}."
            
        removed_item = lines.pop(item_number - 1)
        
        with open(TODO_FILE, "w") as f:
            f.writelines(lines)
            
        return f"🗑️ Removed: {removed_item.strip()}"
    except Exception as e:
        return f"❌ Error deleting item: {e}"

@function_tool
async def set_alarm(seconds: int, reminder_text: str = "Alarm") -> str:
    """
    Sets a background timer/alarm for a specific number of seconds.
    When the time is up, it will print a message and beep (if possible).
    """
    # Note: In a real agent, we might want to callback to the session to speak.
    # For now, we spawn a background task.
    asyncio.create_task(_alarm_countdown(seconds, reminder_text))
    return f"⏰ Alarm set for {seconds} seconds."

async def _alarm_countdown(seconds: int, text: str):
    await asyncio.sleep(seconds)
    logger.info(f"⏰ ALARM: {text}")
    print(f"\n\n⏰⏰⏰ ALARM TRIGGERED: {text} ⏰⏰⏰\n\n")
    # Try system beep
    try:
        import winsound
        winsound.Beep(1000, 1000) # Frequency 1000Hz, Duration 1000ms
    except ImportError:
        print('\a') # Terminal beep fallback
