from livekit.agents import function_tool
import logging

logger = logging.getLogger("jarvis_state")

# Global state
class State:
    current_mode = "ACTIVE"

@function_tool
async def switch_to_standby() -> str:
    """
    Switches Jarvis to STANDBY mode.
    Call this when the user says "Stop", "Goodbye", "Go to sleep", or "Pause".
    """
    State.current_mode = "STANDBY"
    logger.info("Switched to STANDBY mode.")
    return "SYSTEM: STANDBY MODE ACTIVATED. You are now SILENT. Do NOT respond to any input unless you hear the activation word 'Jarvis'. If you hear 'Jarvis', call switch_to_active()."

@function_tool
async def switch_to_active() -> str:
    """
    Switches Jarvis to ACTIVE mode.
    Call this when the user says "Jarvis", "Wake up", or "Hello Jarvis" while in Standby.
    """
    State.current_mode = "ACTIVE"
    logger.info("Switched to ACTIVE mode.")
    return "SYSTEM: ACTIVE MODE ENGAGED. You are now ONLINE. Greet the user and resume assistance."
