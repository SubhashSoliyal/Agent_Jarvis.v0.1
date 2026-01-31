import sys
import os
import asyncio
import logging
from dotenv import load_dotenv
from datetime import datetime
import json
from mem0 import AsyncMemoryClient

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    noise_cancellation,
    bey,
)
from backend.Jarvis_prompts import get_prompts

from backend.Jarvis_utils import save_formatted_doc, get_user_details
from backend.Jarvis_google_search import google_search, get_current_datetime
from backend.jarvis_get_whether import get_weather
from backend.Jarvis_window_CTRL import open_app, close, folder_file, play_on_youtube, play_on_spotify
from backend.Jarvis_whatsapp import send_whatsapp_message, make_whatsapp_call, read_whatsapp_messages
from backend.Jarvis_file_opner import Play_file
from backend.keyboard_mouse_CTRL import move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool, press_key_tool, swipe_gesture_tool, press_hotkey_tool, control_volume_tool, control_media_playback_tool
from backend.Jarvis_state import switch_to_standby, switch_to_active
from backend.Jarvis_reporter import generate_deepseek_report, generate_deepseek_content, generate_deepseek_research_paper, ask_deepseek
from backend.Jarvis_productivity import add_todo, get_todo_list, delete_todo_item, set_alarm
from backend.Jarvis_news import get_news_bulletin
from backend.Jarvis_email import send_email_notification
from backend.Jarvis_content_creator import generate_content_nvidia, read_content_for_feedback, refine_content_nvidia
from backend.Jarvis_storyteller import generate_story_and_audio
from backend.Jarvis_downloader import download_paper_or_document
from backend.Jarvis_testbook import automate_testbook
from backend.Jarvis_memory import remember, recall

load_dotenv()

logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)

if not os.getenv("GOOGLE_API_KEY"):
    logger.error("GOOGLE_API_KEY is not set. Please check your .env file.")

# Enable debug logging for Bey
logging.getLogger("livekit.plugins.bey").setLevel(logging.DEBUG)


class Assistant(Agent):
    def __init__(self, instructions: str) -> None:
        super().__init__(instructions=instructions,
                         tools=[
                            google_search,
                            get_current_datetime,
                            get_weather,
                            switch_to_standby,
                            switch_to_active,
                            add_todo,
                            get_todo_list,
                            delete_todo_item,
                            set_alarm,
                            get_news_bulletin,
                            generate_deepseek_report,
                            generate_deepseek_content,
                            generate_deepseek_research_paper,
                            open_app,
                            close, 
                            folder_file,
                            play_on_youtube,
                            play_on_spotify,
                            Play_file,
                            move_cursor_tool,
                            mouse_click_tool,
                            scroll_cursor_tool,
                            type_text_tool,
                            press_key_tool,
                            press_hotkey_tool,
                            control_volume_tool,
                            swipe_gesture_tool,
                            control_media_playback_tool,
                            generate_content_nvidia,
                            read_content_for_feedback,
                            refine_content_nvidia,
                            send_email_notification,
                            get_user_details,
                            send_whatsapp_message,
                            make_whatsapp_call,
                            read_whatsapp_messages,
                            generate_story_and_audio,
                            download_paper_or_document,
                            automate_testbook,
                            remember,
                            recall
                         ]
                         )

async def entrypoint(ctx: agents.JobContext):
    # Determine gender and voice
    avatar_gender = os.getenv("AVATAR_GENDER", "male").lower()
    voice_name = "Aoede" if avatar_gender == "female" else "Charon"
    
    # Get dynamic prompts
    behavior_prompts, Reply_prompts = get_prompts(gender=avatar_gender)
    
    logger.info(f"Starting agent with Gender: {avatar_gender}, Voice: {voice_name}")

    # --- Memory Integration (mem0) ---
    user_name = os.getenv("USER_NAME", "Subhash") 
    memory_str = ""
    mem0 = None
    
    try:
        mem0 = AsyncMemoryClient()
        results = await mem0.get_all(user_id=user_name)
        if results:
             # Sort by date if available, or just take them
             current_memories = []
             for r in results:
                 date_str = r.get("updated_at", "").split("T")[0] if r.get("updated_at") else "Unknown Date"
                 current_memories.append(f"- [{date_str}] {r['memory']}")
             
             memory_list_str = "\n".join(current_memories)
             behavior_prompts += f"\n\n### Long-term Memories (Context about {user_name}):\n{memory_list_str}\n"
             logger.info(f"Loaded {len(current_memories)} memories into context.")
    except Exception as e:
        logger.warning(f"Failed to load memories: {e}")

    async def shutdown_hook(chat_ctx, mem0_client, known_memories):
        if not mem0_client:
             return
        try:
             logger.info("Shutting down... Saving chat context to memory.")
             messages_to_save = []
             
             # chat_ctx.items is list of ChatMessage
             for item in chat_ctx.items:
                 content = "".join(item.content) if isinstance(item.content, list) else str(item.content)
                 
                 # Skip if content is just the injected memory block
                 if known_memories and known_memories in content:
                     continue
                 
                 if item.role in ("user", "assistant"):
                     messages_to_save.append({"role": item.role, "content": content.strip()})
             
             if messages_to_save:
                 logger.info(f"Saving {len(messages_to_save)} messages to memory...")
                 await mem0_client.add(messages_to_save, user_id=user_name)
                 logger.info("Memory save complete.")
             else:
                 logger.info("No new messages to save.")
                 
        except Exception as e:
             logger.error(f"Error in memory shutdown hook: {e}")
    # ---------------------------------

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice=voice_name
        )
    )

    # Determine if avatar should be enabled
    # Parsing logic: strip whitespace and check for 'true'
    enable_avatar_str = os.getenv("ENABLE_BEY_AVATAR", "true").strip().lower()
    enable_avatar = enable_avatar_str == "true"
    avatar = None

    if enable_avatar:
        avatar = bey.AvatarSession(
            api_key=os.getenv("BEY_API_KEY"),
            avatar_id=os.getenv("BEY_AVATAR_ID"),
        )
        # Enable debug logging for Bey
        logging.getLogger("livekit.plugins.bey").setLevel(logging.DEBUG)
    
    # Determine if video should be enabled based on console mode
    is_console_mode = "console" in sys.argv or os.getenv("AGENT_MODE") == "console"
    is_dev_mode = "dev" in sys.argv
    # Default to False for video to prevent 1008 Policy Violation errors unless explicitly enabled
    video_env = os.getenv("ENABLE_VIDEO", "false").lower() == "true"
    video_enabled = video_env
    
    logger.info(f"Starting agent with video_enabled={video_enabled} (Console Mode: {is_console_mode}, Dev Mode: {is_dev_mode}, Avatar Enabled: {enable_avatar})")

    # Start the avatar and wait for it to join (as per user screenshot)
    if enable_avatar and avatar:
        try:
            logger.info("Starting Bey Avatar session...")
            await avatar.start(session, room=ctx.room)
            logger.info("Bey Avatar session started successfully.")
        except Exception as e:
            logger.error(f"Failed to start Bey Avatar: {e}", exc_info=True)

    await session.start(
        room=ctx.room,
        agent=Assistant(instructions=behavior_prompts),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            video_enabled=video_enabled
        ),
    )

    await ctx.connect()
    
    # Get current real-time and date
    current_time_str = datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
    formatted_reply_prompts = Reply_prompts.format(current_time_str=current_time_str)

    # Retry mechanism for initial greeting
    for attempt in range(1, 4):
        try:
            logger.info(f"Generating initial reply (Attempt {attempt}/3)...")
            await session.generate_reply(
                instructions=formatted_reply_prompts
            )
            break # Success
        except Exception as e:
            logger.error(f"Failed to generate initial reply (Attempt {attempt}): {e}")
            if attempt == 3:
                 logger.error("All greeting attempts failed. Agent remains active but silent.")
            else:
                 await asyncio.sleep(2) # Wait before retry 

    # Register shutdown hook to save memories
    ctx.add_shutdown_callback(lambda: asyncio.create_task(shutdown_hook(session.chat_ctx, mem0, memory_str))) 


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
