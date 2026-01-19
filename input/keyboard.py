"""
Keyboard automation combining pyautogui and pywinauto.

Provides reliable text input and hotkey support for
TWS automation.
"""

from typing import List, Optional, Union
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


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

    def hotkey(self, *keys: str) -> None:
        """
        Press key combination.

        Uses pywinauto.keyboard.send_keys() instead of pyautogui.hotkey()
        for reliable hotkey support in Java Swing applications (TWS).

        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c').

        Example:
            keyboard.hotkey('ctrl', 'shift', 's')  # Ctrl+Shift+S
            keyboard.hotkey('alt', 'f4')           # Alt+F4
        """
        from pywinauto.keyboard import send_keys

        # Build pywinauto format: modifiers + key
        # e.g., ('ctrl', 'shift', 'b') -> '^+b'
        modifiers = ''
        final_key = ''

        for key in keys:
            key_lower = key.lower()
            if key_lower in self.MODIFIER_KEYS:
                modifiers += self.MODIFIER_KEYS[key_lower]
            elif key_lower in self.SPECIAL_KEYS:
                final_key = self.SPECIAL_KEYS[key_lower]
            else:
                final_key = key.lower()

        send_keys(f'{modifiers}{final_key}')

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
