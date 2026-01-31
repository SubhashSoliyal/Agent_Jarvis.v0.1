# Jarvis v3.0 - Advanced AI Agent

Jarvis v3.0 is a sophisticated desktop AI agent capable of real-time voice interaction, autonomous web research, media control, and application automation. Built with LiveKit, Google Gemini, and DeepSeek integration.

## 🚀 Features

- **Real-time Voice Interaction**: Talk to Jarvis naturally using LiveKit's real-time audio pipeline.
- **Deep Research**: autonomously browse the web and generate comprehensive reports using DeepSeek R1 automation.
- **Media Controls**: Control Spotify and YouTube (Play, Pause, Next, Previous) with voice commands.
- **Desktop Automation**: Open apps, manage files, and control windows.
- **Memory**: Remembers user preferences and past conversations (powered by Mem0).
- **Vision**: "See" the screen or webcam feed to understand context.

## 🛠️ Installation

### Prerequisites
- Python 3.10 or higher
- A LiveKit Cloud project (or local server)
- Google Gemini API Key
- Chrome Browser (for automation)

### Setup Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/SubhashSoliyal/Agent_Jarvis.v0.1.git
   cd Jarvis.v3.0/Jarvis.v3.0
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: You may need `playwright install` if running for the first time.*

3. **Configure Environment**
   - Copy `.env.example` to `.env`:
     ```bash
     copy .env.example .env
     ```
   - Edit `.env` and fill in your API keys (LiveKit, Gemini, etc.).

## 💻 Usage

### Starting the Agent
To launch the agent simply run:

```bash
python agent.py
```

### Connect
Open the [LiveKit Agent Playground](https://agents-playground.livekit.io/) (or your own frontend), connect to your LiveKit project, and start talking!

### Commands
- **"Play some music"** -> Starts Spotify/YouTube.
- **"Pause music", "Next song"** -> Controls playback.
- **"Generate a report on [topic]"** -> Uses DeepSeek to write a document.
- **"Open Notepad"** -> Launches applications.

## 📂 Project Structure
- `agent.py`: Main entry point and agent logic.
- `backend/`: Core functionality modules.
    - `Jarvis_window_CTRL.py`: Desktop/Window control.
    - `Jarvis_reporter.py`: DeepSeek automation & reporting.
    - `keyboard_mouse_CTRL.py`: Input simulation.
- `commands_manual.md`: Detailed list of supported commands.

## 📜 License
[MIT](LICENSE)
