import pyautogui
import asyncio
import time
import logging
from datetime import datetime
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
from typing import List
from livekit.agents import function_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------
# SafeController Class
# ---------------------
class SafeController:
    def __init__(self):
        self.active = False
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.valid_keys = set("abcdefghijklmnopqrstuvwxyz1234567890")
        self.special_keys = {
            "enter": Key.enter, "space": Key.space, "tab": Key.tab,
            "shift": Key.shift, "ctrl": Key.ctrl, "alt": Key.alt,
            "esc": Key.esc, "backspace": Key.backspace, "delete": Key.delete,
            "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
            "caps_lock": Key.caps_lock, "cmd": Key.cmd, "win": Key.cmd,
            "home": Key.home, "end": Key.end,
            "page_up": Key.page_up, "page_down": Key.page_down
        }

    def resolve_key(self, key):
        return self.special_keys.get(key.lower(), key)

    def activate(self, token=None):
        if token != "my_secret_token":
            logger.warning("Activation attempt failed.")
            return
        self.active = True
        logger.info("Controller activated.")

    def deactivate(self):
        self.active = False
        logger.info("Controller deactivated.")

    def is_active(self):
        return self.active

    # ---------------------------------------------------------
    # Helper to run blocking input commands in a separate thread
    # ---------------------------------------------------------
    async def _run_blocking(self, func, *args):
        if not self.is_active():
            return "🛑 Controller is inactive."
        try:
            return await asyncio.to_thread(func, *args)
        except Exception as e:
            logger.error(f"Input verification error: {e}")
            return f"❌ Error: {e}"

    # -----------------------
    # Implementation Methods
    # -----------------------
    def _move_cursor_impl(self, direction: str, distance: int):
        x, y = self.mouse.position
        if direction == "left": self.mouse.position = (x - distance, y)
        elif direction == "right": self.mouse.position = (x + distance, y)
        elif direction == "up": self.mouse.position = (x, y - distance)
        elif direction == "down": self.mouse.position = (x, y + distance)
        logger.info(f"Mouse moved {direction}")
        return f"🖱️ Moved mouse {direction}."

    async def move_cursor(self, direction: str, distance: int = 100):
        return await self._run_blocking(self._move_cursor_impl, direction, distance)

    def _mouse_click_impl(self, button: str):
        if button == "left": self.mouse.click(Button.left, 1)
        elif button == "right": self.mouse.click(Button.right, 1)
        elif button == "double": self.mouse.click(Button.left, 2)
        logger.info(f"Mouse clicked: {button}")
        return f"🖱️ {button.capitalize()} click."

    async def mouse_click(self, button: str = "left"):
        return await self._run_blocking(self._mouse_click_impl, button)

    def _scroll_cursor_impl(self, direction: str, amount: int):
        try:
            if direction == "up": self.mouse.scroll(0, amount)
            elif direction == "down": self.mouse.scroll(0, -amount)
        except:
            pyautogui.scroll(amount * 100 if direction == "up" else -amount * 100)
        logger.info(f"Mouse scrolled {direction}")
        return f"🖱️ Scrolled {direction}"

    async def scroll_cursor(self, direction: str, amount: int = 10):
        return await self._run_blocking(self._scroll_cursor_impl, direction, amount)

    def _type_text_impl(self, text: str):
        for char in text:
            if not char.isprintable(): continue
            try:
                self.keyboard.press(char)
                self.keyboard.release(char)
                time.sleep(0.01) # Tiny sleep for stability between keystrokes
            except Exception: continue
        logger.info(f"Typed text: {text}")
        return f"⌨️ Typed: {text}"

    async def type_text(self, text: str):
        return await self._run_blocking(self._type_text_impl, text)

    def _press_key_impl(self, key: str):
        if key.lower() not in self.special_keys and key.lower() not in self.valid_keys:
            return f"❌ Invalid key: {key}"
        k = self.resolve_key(key)
        try:
            self.keyboard.press(k)
            self.keyboard.release(k)
        except Exception as e:
            return f"❌ Failed key: {key} — {e}"
        logger.info(f"Pressed key: {key}")
        return f"⌨️ Key '{key}' pressed."

    async def press_key(self, key: str):
        return await self._run_blocking(self._press_key_impl, key)

    def _press_hotkey_impl(self, keys: List[str]):
        resolved = []
        for k in keys:
            if k.lower() not in self.special_keys and k.lower() not in self.valid_keys:
                return f"❌ Invalid key in hotkey: {k}"
            resolved.append(self.resolve_key(k))

        for k in resolved: self.keyboard.press(k)
        for k in reversed(resolved): self.keyboard.release(k)
        logger.info(f"Pressed hotkey: {' + '.join(keys)}")
        return f"⌨️ Hotkey {' + '.join(keys)} pressed."

    async def press_hotkey(self, keys: List[str]):
        return await self._run_blocking(self._press_hotkey_impl, keys)

    def _control_volume_impl(self, action: str):
        if action == "up": pyautogui.press("volumeup")
        elif action == "down": pyautogui.press("volumedown")
        elif action == "mute": pyautogui.press("volumemute")
        logger.info(f"Volume control: {action}")
        return f"🔊 Volume {action}."

    async def control_volume(self, action: str):
        return await self._run_blocking(self._control_volume_impl, action)

    def _swipe_gesture_impl(self, direction: str):
        screen_width, screen_height = pyautogui.size()
        x, y = screen_width // 2, screen_height // 2
        try:
            distance = 200
            duration = 0.5
            if direction == "up": 
                pyautogui.moveTo(x, y + distance)
                pyautogui.dragTo(x, y - distance, duration=duration)
            elif direction == "down": 
                pyautogui.moveTo(x, y - distance)
                pyautogui.dragTo(x, y + distance, duration=duration)
            elif direction == "left": 
                pyautogui.moveTo(x + distance, y)
                pyautogui.dragTo(x - distance, y, duration=duration)
            elif direction == "right": 
                pyautogui.moveTo(x - distance, y)
                pyautogui.dragTo(x + distance, y, duration=duration)
        except Exception as e:
            logger.error(f"Swipe error: {e}")
            return f"❌ Swipe failed: {e}"
        
        logger.info(f"Swipe gesture: {direction}")
        return f"🖱️ Swipe {direction} done."

    async def swipe_gesture(self, direction: str):
        return await self._run_blocking(self._swipe_gesture_impl, direction)

    def _control_media_impl(self, action: str):
        if action == "play_pause": pyautogui.press("playpause")
        elif action == "next": pyautogui.press("nexttrack")
        elif action == "previous": pyautogui.press("prevtrack")
        elif action == "stop": pyautogui.press("stop")
        logger.info(f"Media control: {action}")
        return f"⏯️ Media {action}."

    async def control_media(self, action: str):
        return await self._run_blocking(self._control_media_impl, action)

    # ------------------------------
    # LiveKit Tool Wrappers Section
    # ------------------------------

    # ... (existing wrappers)

# ... (End of SafeController methods)

# ------------------------------
# LiveKit Tool Wrappers Section
# ------------------------------

controller = SafeController()

async def with_temporary_activation(fn, *args, **kwargs):
    # Minimal activation wrapper without arbitrary sleeps
    controller.activate("my_secret_token")
    try:
        result = await fn(*args, **kwargs)
        return result
    finally:
        controller.deactivate()

@function_tool
async def move_cursor_tool(direction: str, distance: int = 100):
    return await with_temporary_activation(controller.move_cursor, direction, distance)

@function_tool
async def mouse_click_tool(button: str = "left"):
    return await with_temporary_activation(controller.mouse_click, button)

@function_tool
async def scroll_cursor_tool(direction: str, amount: int = 10):
    return await with_temporary_activation(controller.scroll_cursor, direction, amount)

@function_tool
async def type_text_tool(text: str):
    return await with_temporary_activation(controller.type_text, text)

@function_tool
async def press_key_tool(key: str):
    return await with_temporary_activation(controller.press_key, key)

@function_tool
async def press_hotkey_tool(keys: List[str]):
    return await with_temporary_activation(controller.press_hotkey, keys)

@function_tool
async def control_volume_tool(action: str):
    return await with_temporary_activation(controller.control_volume, action)

@function_tool
async def swipe_gesture_tool(direction: str):
    return await with_temporary_activation(controller.swipe_gesture, direction)

@function_tool
async def control_media_playback_tool(action: str):
    """
    Control media playback.
    Args:
        action: 'play_pause', 'next', 'previous', or 'stop'.
    """
    return await with_temporary_activation(controller.control_media, action)
