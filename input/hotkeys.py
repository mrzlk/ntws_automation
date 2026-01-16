"""
Integration with TWS built-in hotkey system.

Provides access to TWS keyboard shortcuts for
fast, reliable automation of common actions.

Note: Actual hotkey config is encrypted in HotKeysSettings.json.ibgzenc
Default bindings are based on IBKR documentation.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List, TYPE_CHECKING
from enum import Enum
import logging

if TYPE_CHECKING:
    from .keyboard import Keyboard

logger = logging.getLogger(__name__)


class TWSAction(Enum):
    """
    Known TWS hotkey actions.

    These actions correspond to built-in TWS
    keyboard shortcuts.
    """
    # Order actions
    BUY = "buy"
    SELL = "sell"
    TRANSMIT_ORDER = "transmit"
    CANCEL_ORDER = "cancel"
    CANCEL_ALL = "cancel_all"
    MODIFY_ORDER = "modify"

    # Chart actions
    OPEN_CHART = "open_chart"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    RESET_CHART = "reset_chart"

    # Navigation
    SEARCH_SYMBOL = "search_symbol"
    PORTFOLIO = "portfolio"
    ORDERS = "orders"
    TRADES = "trades"
    WATCHLIST = "watchlist"

    # Window management
    NEW_WINDOW = "new_window"
    CLOSE_WINDOW = "close_window"
    TILE_WINDOWS = "tile_windows"
    SETTINGS = "settings"

    # Data
    REFRESH = "refresh"
    EXPORT = "export"


@dataclass
class HotkeyBinding:
    """
    Hotkey binding definition.

    Attributes:
        action: The TWS action this binding triggers.
        modifiers: Modifier keys (ctrl, shift, alt).
        key: The main key.
        description: Human-readable description.
    """
    action: TWSAction
    modifiers: List[str]
    key: str
    description: str = ""

    def to_sequence(self) -> tuple:
        """Convert to pyautogui hotkey sequence."""
        return tuple(self.modifiers + [self.key])

    def __str__(self) -> str:
        mods = '+'.join(m.capitalize() for m in self.modifiers)
        if mods:
            return f"{mods}+{self.key.upper()}"
        return self.key.upper()


class TWSHotkeys:
    """
    TWS hotkey manager.

    Manages keyboard shortcuts for TWS actions.
    Provides default bindings based on IBKR documentation
    with support for custom overrides.

    Attributes:
        DEFAULT_HOTKEYS: Default TWS keyboard shortcuts.
    """

    # Default TWS hotkeys (from IBKR documentation)
    DEFAULT_HOTKEYS: Dict[TWSAction, HotkeyBinding] = {
        # Order actions
        TWSAction.BUY: HotkeyBinding(
            TWSAction.BUY, ['alt'], 'b', 'Create buy order'
        ),
        TWSAction.SELL: HotkeyBinding(
            TWSAction.SELL, ['alt'], 's', 'Create sell order'
        ),
        TWSAction.TRANSMIT_ORDER: HotkeyBinding(
            TWSAction.TRANSMIT_ORDER, ['alt'], 't', 'Transmit order'
        ),
        TWSAction.CANCEL_ORDER: HotkeyBinding(
            TWSAction.CANCEL_ORDER, ['alt'], 'd', 'Cancel selected order'
        ),
        TWSAction.CANCEL_ALL: HotkeyBinding(
            TWSAction.CANCEL_ALL, ['alt'], 'c', 'Cancel all orders'
        ),

        # Navigation
        TWSAction.SEARCH_SYMBOL: HotkeyBinding(
            TWSAction.SEARCH_SYMBOL, ['ctrl'], 'f', 'Search for symbol'
        ),
        TWSAction.PORTFOLIO: HotkeyBinding(
            TWSAction.PORTFOLIO, ['alt'], 'p', 'Open portfolio'
        ),
        TWSAction.ORDERS: HotkeyBinding(
            TWSAction.ORDERS, ['alt'], 'o', 'Open orders'
        ),

        # Window
        TWSAction.CLOSE_WINDOW: HotkeyBinding(
            TWSAction.CLOSE_WINDOW, ['alt'], 'f4', 'Close window'
        ),

        # Data
        TWSAction.REFRESH: HotkeyBinding(
            TWSAction.REFRESH, [], 'f5', 'Refresh data'
        ),
    }

    def __init__(
        self,
        keyboard: 'Keyboard',
        custom_bindings: Dict = None
    ):
        """
        Initialize hotkey manager.

        Args:
            keyboard: Keyboard automation instance.
            custom_bindings: Optional custom hotkey overrides.
        """
        self.keyboard = keyboard
        self.bindings: Dict[TWSAction, HotkeyBinding] = dict(self.DEFAULT_HOTKEYS)

        if custom_bindings:
            self._load_custom_bindings(custom_bindings)

    def _load_custom_bindings(self, bindings: Dict) -> None:
        """Load custom hotkey bindings."""
        for action_name, binding_data in bindings.items():
            try:
                action = TWSAction(action_name)
                self.bindings[action] = HotkeyBinding(
                    action=action,
                    modifiers=binding_data.get('modifiers', []),
                    key=binding_data.get('key', ''),
                    description=binding_data.get('description', '')
                )
            except ValueError:
                logger.warning(f"Unknown action: {action_name}")

    def execute(self, action: TWSAction) -> bool:
        """
        Execute TWS action via hotkey.

        Args:
            action: The action to execute.

        Returns:
            True if hotkey was sent, False if action not bound.
        """
        binding = self.bindings.get(action)
        if not binding:
            logger.warning(f"No binding for action: {action}")
            return False

        try:
            self.keyboard.hotkey(*binding.to_sequence())
            logger.debug(f"Executed hotkey: {binding}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute hotkey {binding}: {e}")
            return False

    def get_binding(self, action: TWSAction) -> Optional[HotkeyBinding]:
        """
        Get binding for action.

        Args:
            action: The action to look up.

        Returns:
            HotkeyBinding or None if not bound.
        """
        return self.bindings.get(action)

    def register(
        self,
        action: TWSAction,
        modifiers: List[str],
        key: str,
        description: str = ""
    ) -> None:
        """
        Register or override hotkey binding.

        Args:
            action: The TWS action.
            modifiers: Modifier keys.
            key: Main key.
            description: Optional description.
        """
        self.bindings[action] = HotkeyBinding(
            action=action,
            modifiers=modifiers,
            key=key,
            description=description
        )

    def register_custom(
        self,
        name: str,
        modifiers: List[str],
        key: str,
        description: str = ""
    ) -> TWSAction:
        """
        Register custom action with hotkey.

        For actions not in the default TWSAction enum,
        this creates a dynamic binding.

        Args:
            name: Custom action name.
            modifiers: Modifier keys.
            key: Main key.
            description: Optional description.

        Returns:
            The action (may be existing or None for custom).
        """
        # Try to find matching action
        try:
            action = TWSAction(name)
        except ValueError:
            # Custom action - store with string key
            logger.info(f"Registering custom action: {name}")
            action = None

        if action:
            self.register(action, modifiers, key, description)

        return action

    def list_bindings(self) -> Dict[str, str]:
        """
        List all registered hotkey bindings.

        Returns:
            Dict mapping action names to hotkey strings.
        """
        return {
            action.value: str(binding)
            for action, binding in self.bindings.items()
        }

    # Convenience methods for common actions

    def buy(self) -> bool:
        """Trigger buy order creation."""
        return self.execute(TWSAction.BUY)

    def sell(self) -> bool:
        """Trigger sell order creation."""
        return self.execute(TWSAction.SELL)

    def transmit(self) -> bool:
        """Transmit selected order."""
        return self.execute(TWSAction.TRANSMIT_ORDER)

    def cancel(self) -> bool:
        """Cancel selected order."""
        return self.execute(TWSAction.CANCEL_ORDER)

    def cancel_all(self) -> bool:
        """Cancel all orders."""
        return self.execute(TWSAction.CANCEL_ALL)

    def search(self) -> bool:
        """Open symbol search."""
        return self.execute(TWSAction.SEARCH_SYMBOL)

    def refresh(self) -> bool:
        """Refresh data."""
        return self.execute(TWSAction.REFRESH)
