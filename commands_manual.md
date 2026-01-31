# Jarvis Agent Commands Manual

This document provides a comprehensive list of commands and capabilities available to the Jarvis Agent.

## Core Capabilities

### General Assistance & Search
- **Internet Search**: "Search specifically for [query]", "Find the latest news on [topic]".
    - *Tool*: `google_search`
- **Time & Date**: "What time is it?", "What is today's date?" (Often handled automatically in greeting).
- **Weather**: "What's the weather like in [City]?", "Is it raining?".
    - *Tool*: `get_weather`

### Memory & Personalization
- **Remembering**: "Remember that I like...", "Note that my birthday is...".
    - *Tool*: `remember`
- **Recalling**: "What did I tell you about...?", "What is my favorite...?"
    - *Tool*: `recall`
- **User Details**: "What is my college ID?", "What is my address?"
    - *Tool*: `get_user_details`

### Mode Control
- **Standby Mode**: "Stop", "Goodbye", "Go to sleep".  (Agent stops listening/responding).
    - *Tool*: `switch_to_standby`
- **Wake Up**: "Jarvis", "Wake up". (Agent resumes).
    - *Tool*: `switch_to_active`

## Productivity Tools

### Task Management
- **Add Todo**: "Add [task] to my todo list".
    - *Tool*: `add_todo`
- **View Todos**: "Show my todo list", "What do I have to do?".
    - *Tool*: `get_todo_list`
- **Delete Todo**: "Remove [task] from the list", "Mark [task] as done".
    - *Tool*: `delete_todo_item`
- **Alarms**: "Set an alarm for [time]", "Wake me up at [time]".
    - *Tool*: `set_alarm`

### DeepSeek Research & Content
- **Quick Answers**: "Ask DeepSeek about...", "Explain [concept]".
    - *Tool*: `ask_deepseek`
- **Detailed Reports**: "Create a report on [topic]", "Generate a research paper about [topic]".
    - *Tool*: `generate_deepseek_report`, `generate_deepseek_research_paper`
- **Content Generation**: "Write an article/blog about [topic]".
    - *Tool*: `generate_deepseek_content`
- **Document Downloading**: "Download this paper", "Find and download documents about [topic]".
    - *Tool*: `download_paper_or_document`

### News & Email
- **News**: "Teil me the news", "Get the latest headlines".
    - *Tool*: `get_news_bulletin`
- **Email**: "Send an email to [recipient] saying [message]".
    - *Tool*: `send_email_notification`

## Computer Control

### App & File Management
- **Open Apps**: "Open [App Name] (e.g., Code, Chrome, WhatsApp)".
    - *Tool*: `open_app`
- **Close Apps**: "Close [App Name]".
    - *Tool*: `close`
    - **Note**: Use this to close the *entire application window*. To just stop music/video, say "Stop music" using the Media Controls.
- **File System**: "Open the folder [path]", "Open the file [filename]".
    - *Tool*: `folder_file`, `Play_file`

### Playback & Media
- **YouTube**: "Play [song/video] on YouTube".
    - *Tool*: `play_on_youtube`
- **Spotify**: "Play [song] on Spotify".
    - *Tool*: `play_on_spotify`
- **Volume**: "Increase volume", "Mute".
    - *Tool*: `control_volume_tool`
- **Media Controls** (NEW):
    - "Pause", "Resume", "Stop music".
    - "Next song", "Skip", "Previous song".
    - *Tool*: `control_media_playback_tool`

### Peripheral Control
- **Mouse/Keyboard**: The agent can move the mouse, click, scroll, type text, and press keys.
    - *Tools*: `move_cursor_tool`, `mouse_click_tool`, `type_text_tool`, `press_key_tool`, `swipe_gesture_tool`

## Integrations

### WhatsApp
- **Send Message**: "Send a WhatsApp message to [Name] saying [Message]".
    - *Tool*: `send_whatsapp_message`
- **Call**: "Call [Name] on WhatsApp".
    - *Tool*: `make_whatsapp_call`
- **Read Messages**: "Read my WhatsApp messages".
    - *Tool*: `read_whatsapp_messages`

### Content Creation (NVIDIA)
- **Generate**: "Generate content about [topic] using NVIDIA".
    - *Tool*: `generate_content_nvidia`
- **Refine**: "Refine this content...".
    - *Tool*: `refine_content_nvidia`
- **Feedback**: "Read this for feedback".
    - *Tool*: `read_content_for_feedback`

### Storytelling
- **Stories**: "Tell me a story about...", "Generate an audio story".
    - *Tool*: `generate_story_and_audio`

### Testbook (Exam Prep)
- **Automation**: "Login to Testbook", "Search for SSC exams on Testbook", "Check my dashboard".
    - *Tool*: `automate_testbook`
