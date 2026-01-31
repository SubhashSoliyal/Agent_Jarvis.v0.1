import sys
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    noise_cancellation,
)
from backend.Jarvis_prompts import behavior_prompts, Reply_prompts
from backend.Jarvis_utils import save_formatted_doc, get_user_details
from backend.Jarvis_google_search import google_search, get_current_datetime
from backend.jarvis_get_whether import get_weather
from backend.Jarvis_window_CTRL import open_app, close, folder_file, play_on_youtube, play_on_spotify
from backend.Jarvis_whatsapp import send_whatsapp_message, make_whatsapp_call, read_whatsapp_messages
from backend.Jarvis_file_opner import Play_file
from backend.keyboard_mouse_CTRL import move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool, press_key_tool, swipe_gesture_tool, press_hotkey_tool, control_volume_tool
from backend.Jarvis_state import switch_to_standby, switch_to_active
from backend.Jarvis_reporter import generate_deepseek_report, generate_deepseek_content, generate_deepseek_research_paper, ask_deepseek
from backend.Jarvis_productivity import add_todo, get_todo_list, delete_todo_item, set_alarm
from backend.Jarvis_news import get_news_bulletin
from backend.Jarvis_email import send_email_notification
from backend.Jarvis_content_creator import generate_content_nvidia, read_content_for_feedback, refine_content_nvidia
from backend.Jarvis_storyteller import generate_story_and_audio

load_dotenv()

logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)

if not os.getenv("GOOGLE_API_KEY"):
    logger.error("GOOGLE_API_KEY is not set. Please check your .env file.")



class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=behavior_prompts,
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
                            generate_deepseek_content, # New tool for content
                            generate_deepseek_research_paper,
                            open_app, #ये apps ओपन करने के लिए हैं
                            close, 
                            folder_file, #ये folder ओपन करने के लिए है
                            play_on_youtube, # YouTube पर play करने के लिए
                            play_on_spotify, # Spotify पर play करने के लिए
                            Play_file,  #ये file रन करने के लिए है जैसे कि MP4, MP3, PDF, PPT, img, png etc.
                            move_cursor_tool, #ये cursor move करने के लिए है
                            mouse_click_tool, #ये mouse click करने के लिए है
                            scroll_cursor_tool, #ये cursor scroll करने के लिए है
                            type_text_tool, #ये text type करने के लिए है
                            press_key_tool, #ये key press करने के लिए है
                            press_hotkey_tool, #ये hotkey press करने के लिए है
                            control_volume_tool, #ये volume control करने के लिए है
                            swipe_gesture_tool, #ये gesture wipe करने के लिए है 
                            generate_content_nvidia,
                            read_content_for_feedback,
                            refine_content_nvidia,
                            send_email_notification,
                            get_user_details,
                            send_whatsapp_message,
                            make_whatsapp_call,
                            read_whatsapp_messages,
                            generate_story_and_audio
                         ]
                         )


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Charon"
        )
    )
    
    # Determine if video should be enabled based on console mode
    is_console_mode = "console" in sys.argv
    video_enabled = not is_console_mode
    logger.info(f"Starting agent with video_enabled={video_enabled} (Console Mode: {is_console_mode})")

    await session.start(
        room=ctx.room,
        agent=Assistant(),
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



if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

