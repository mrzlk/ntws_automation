"""
Keyboard automation combining pyautogui and Win32 SendInput.

Provides reliable text input and hotkey support for
TWS automation (Java Swing application).

Note: Hotkeys use Win32 SendInput API directly because:
- pyautogui.hotkey() doesn't work reliably with Java Swing
- pywinauto.send_keys() messages don't reach Java applications
- SendInput injects events into system input queue, works with any app
"""

from typing import List, Optional, Union
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import time
import logging

logger = logging.getLogger(__name__)

# Win32 SendInput constants and structures
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002


class KEYBDINPUT(ctypes.Structure):
    """Win32 KEYBDINPUT structure for SendInput."""
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))
    ]


class INPUT(ctypes.Structure):
    """Win32 INPUT structure for SendInput."""
    _fields_ = [
        ('type', wintypes.DWORD),
        ('ki', KEYBDINPUT),
        ('padding', ctypes.c_ubyte * 8)
    ]


class Keyboard:
    """
    Keyboard automation with multiple backends.

    Supports:
    - Character-by-character typing
    - Special key combinations
    - Modifier key holding
    - PyWinAuto format key sequences

    Attributes:
        SPECIAL_KEYS: Mapping of key names to PyWinAuto format.
        typing_interval: Delay between keystrokes.
    """

    SPECIAL_KEYS = {
        'enter': '{ENTER}',
        'return': '{ENTER}',
        'tab': '{TAB}',
        'escape': '{ESC}',
        'esc': '{ESC}',
        'backspace': '{BACKSPACE}',
        'delete': '{DELETE}',
        'del': '{DELETE}',
        'insert': '{INSERT}',
        'up': '{UP}',
        'down': '{DOWN}',
        'left': '{LEFT}',
        'right': '{RIGHT}',
        'home': '{HOME}',
        'end': '{END}',
        'pageup': '{PGUP}',
        'pagedown': '{PGDN}',
        'space': ' ',
        'f1': '{F1}', 'f2': '{F2}', 'f3': '{F3}', 'f4': '{F4}',
        'f5': '{F5}', 'f6': '{F6}', 'f7': '{F7}', 'f8': '{F8}',
        'f9': '{F9}', 'f10': '{F10}', 'f11': '{F11}', 'f12': '{F12}',
    }

    MODIFIER_KEYS = {
        'ctrl': '^',
        'control': '^',
        'alt': '%',
        'shift': '+',
        'win': '#',
        'windows': '#',
    }

    # Virtual key codes for Win32 SendInput
    VK_CODES = {
        # Modifiers
        'ctrl': 0x11, 'control': 0x11,
        'alt': 0x12, 'menu': 0x12,
        'shift': 0x10,
        'win': 0x5B, 'windows': 0x5B,
        # Letters
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
        'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
        'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
        'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
        'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
        'z': 0x5A,
        # Numbers
        '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
        '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
        # Function keys
        'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
        'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
        'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
        # Special keys
        'enter': 0x0D, 'return': 0x0D,
        'tab': 0x09,
        'escape': 0x1B, 'esc': 0x1B,
        'backspace': 0x08,
        'delete': 0x2E, 'del': 0x2E,
        'insert': 0x2D,
        'home': 0x24, 'end': 0x23,
        'pageup': 0x21, 'pagedown': 0x22,
        'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
        'space': 0x20,
    }

    def __init__(self, typing_interval: float = 0.02):
        """
        Initialize keyboard automation.

        Args:
            typing_interval: Delay between keystrokes in seconds.
        """
        self.typing_interval = typing_interval

    def type_text(self, text: str, interval: float = None) -> None:
        """
        Type text character by character.

        Uses pyautogui for reliable cross-application typing.

        Args:
            text: Text to type.
            interval: Override default typing interval.
        """
        import pyautogui

        interval = interval or self.typing_interval
        pyautogui.typewrite(text, interval=interval)

    def type_unicode(self, text: str) -> None:
        """
        Type unicode text (supports non-ASCII characters).

        Uses clipboard for reliable unicode input.

        Args:
            text: Unicode text to type.
        """
        import pyperclip
        import pyautogui

        # Save current clipboard
        try:
            original = pyperclip.paste()
        except:
            original = ""

        # Copy text to clipboard and paste
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')

        # Restore clipboard
        try:
            pyperclip.copy(original)
        except:
            pass

    def send_keys(self, keys: str) -> None:
        """
        Send key sequence using pywinauto format.

        Format examples:
        - "{ENTER}" - Enter key
        - "^a" - Ctrl+A
        - "%{F4}" - Alt+F4
        - "+abc" - Shift+abc (ABC)

        Args:
            keys: Key sequence in pywinauto format.
        """
        try:
            from pywinauto.keyboard import send_keys
            send_keys(keys)
        except ImportError:
            logger.warning("pywinauto not available, falling back to pyautogui")
            self._send_keys_fallback(keys)

    def _send_keys_fallback(self, keys: str) -> None:
        """Fallback implementation for send_keys."""
        import pyautogui

        # Simple parsing - handle common cases
        if keys.startswith('^'):
            pyautogui.hotkey('ctrl', keys[1:])
        elif keys.startswith('%'):
            pyautogui.hotkey('alt', keys[1:])
        elif keys.startswith('+'):
            pyautogui.hotkey('shift', keys[1:])
        else:
            pyautogui.typewrite(keys)

    def press(self, key: str) -> None:
        """
        Press and release a single key.

        Args:
            key: Key name (e.g., 'enter', 'tab', 'a').
        """
        import pyautogui

        # Map to special key if needed
        key_lower = key.lower()
        if key_lower in self.SPECIAL_KEYS:
            self.send_keys(self.SPECIAL_KEYS[key_lower])
        else:
            pyautogui.press(key)

    def _send_input_key(self, vk: int, key_up: bool = False) -> None:
        """
        Send a single key event via Win32 SendInput.

        Args:
            vk: Virtual key code.
            key_up: If True, send key release event.
        """
        user32 = ctypes.windll.user32
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.ki.wVk = vk
        inp.ki.dwFlags = KEYEVENTF_KEYUP if key_up else 0
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def hotkey(self, *keys: str) -> None:
        """
        Press key combination using Win32 SendInput.

        Uses SendInput API directly for reliable hotkey support
        in Java Swing applications (TWS). This injects keyboard
        events into the system input queue, working with any application.

        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c').

        Example:
            keyboard.hotkey('ctrl', 'shift', 's')  # Ctrl+Shift+S
            keyboard.hotkey('alt', 'f4')           # Alt+F4
        """
        # Separate modifiers from the final key
        modifiers = []
        final_key = None

        for key in keys:
            key_lower = key.lower()
            if key_lower in ('ctrl', 'control', 'alt', 'menu', 'shift', 'win', 'windows'):
                modifiers.append(key_lower)
            else:
                final_key = key_lower

        if final_key is None:
            logger.warning(f"No final key in hotkey combination: {keys}")
            return

        # Get virtual key codes
        vk_final = self.VK_CODES.get(final_key)
        if vk_final is None:
            logger.error(f"Unknown key: {final_key}")
            return

        vk_modifiers = []
        for mod in modifiers:
            vk = self.VK_CODES.get(mod)
            if vk:
                vk_modifiers.append(vk)

        # Press modifiers
        for vk in vk_modifiers:
            self._send_input_key(vk)

        # Press and release final key
        self._send_input_key(vk_final)
        time.sleep(0.02)
        self._send_input_key(vk_final, key_up=True)

        # Release modifiers (in reverse order)
        for vk in reversed(vk_modifiers):
            self._send_input_key(vk, key_up=True)

    @contextmanager
    def hold(self, key: str):
        """
        Context manager for holding a key.

        Args:
            key: Key to hold during context.

        Example:
            with keyboard.hold('shift'):
                keyboard.press('a')  # Types 'A'
        """
        import pyautogui

        pyautogui.keyDown(key)
        try:
            yield
        finally:
            pyautogui.keyUp(key)

    def key_down(self, key: str) -> None:
        """
        Press and hold a key.

        Args:
            key: Key to press down.
        """
        import pyautogui
        pyautogui.keyDown(key)

    def key_up(self, key: str) -> None:
        """
        Release a held key.

        Args:
            key: Key to release.
        """
        import pyautogui
        pyautogui.keyUp(key)

    def is_pressed(self, key: str) -> bool:
        """
        Check if key is currently pressed.

        Args:
            key: Key to check.

        Returns:
            True if key is pressed.
        """
        try:
            import keyboard as kb
            return kb.is_pressed(key)
        except ImportError:
            logger.warning("keyboard module not available for key state detection")
            return False
