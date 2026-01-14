# NTWS Automation Toolkit - Architecture Overview

## Purpose

GUI automation for IBKR Trader Workstation (Qt/QML app) without official API.
Simulates human input (keyboard, mouse) + reads screen via OCR.

## Project Structure

```
ntws_automation/
├── __init__.py          # NTWSToolkit - main entry point
├── core/                # Window connection, element finding
├── input/               # Keyboard, mouse, hotkeys
├── screen/              # Screenshots, OCR
├── config/              # Settings management
├── actions/             # High-level trading actions
├── utils/               # Logging, retry, validation
└── mcp_server/          # MCP server for Claude integration
```

## Core Interfaces

### 1. Main Toolkit Class

```python
class NTWSToolkit:
    """Main entry point - combines all components."""

    def __init__(self, config_path: str = None):
        self.window: NTWSWindow      # Window manager
        self.keyboard: Keyboard      # Keyboard input
        self.mouse: Mouse            # Mouse input
        self.hotkeys: NTWSHotkeys    # NTWS shortcuts
        self.capture: ScreenCapture  # Screenshots
        self.ocr: OCREngine          # Text recognition
        self.finder: ElementFinder   # UI element finding
        self.actions: ActionRegistry # High-level actions

    def connect(self) -> bool:
        """Connect to running NTWS window."""

    def _verify_paper_trading(self) -> bool:
        """Safety check - verify paper trading mode."""
```

### 2. Action Base Class

```python
@dataclass
class ActionResult:
    success: bool
    message: str = ""
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0

class Action(ABC):
    """Base class for all high-level actions."""

    def __init__(self, toolkit: NTWSToolkit):
        self.toolkit = toolkit

    # Convenience accessors
    @property
    def keyboard(self): return self.toolkit.keyboard
    @property
    def mouse(self): return self.toolkit.mouse
    @property
    def hotkeys(self): return self.toolkit.hotkeys
    @property
    def ocr(self): return self.toolkit.ocr

    @abstractmethod
    def execute(self, **kwargs) -> ActionResult:
        """Execute the action."""

    def validate(self, **kwargs) -> Optional[str]:
        """Validate parameters. Return error message or None."""
```

### 3. Action Registry

```python
class ActionRegistry:
    """Unified access to all actions."""

    def __init__(self, toolkit: NTWSToolkit):
        self._create_order = CreateOrderAction(toolkit)
        self._search_symbol = SearchSymbolAction(toolkit)
        # ... other actions

    # Order actions
    def create_order(self, symbol, side, quantity, ...) -> ActionResult
    def transmit_order(self, confirm=True) -> ActionResult
    def cancel_order(self, order_id=None, cancel_all=False) -> ActionResult

    # Navigation
    def search_symbol(self, symbol, select=True) -> ActionResult
    def open_chart(self, symbol, timeframe='1D') -> ActionResult

    # Portfolio
    def get_portfolio(self) -> ActionResult
    def get_position(self, symbol) -> ActionResult
```

### 4. Exception Hierarchy

```python
NTWSAutomationError          # Base
├── WindowNotFoundError      # NTWS not running
├── ElementNotFoundError     # UI element not found
├── TimeoutError             # Operation timed out
├── ActionFailedError        # High-level action failed
├── OCRError                 # OCR operation failed
├── SafetyError              # Safety check failed
└── ConfigurationError       # Config error
```

### 5. Element Finding Strategies

```python
class FindStrategy(Enum):
    UIA = "uia"           # UI Automation (fast, for accessible elements)
    OCR = "ocr"           # Text recognition (any visible text)
    IMAGE = "image"       # Template matching (fallback)
    POSITION = "position" # Fixed coordinates (last resort)
    HYBRID = "hybrid"     # Combine strategies

@dataclass
class ElementSpec:
    name: Optional[str] = None
    automation_id: Optional[str] = None
    control_type: Optional[str] = None
    text_pattern: Optional[str] = None
    strategy: FindStrategy = FindStrategy.UIA

class ElementFinder:
    def find(self, spec: ElementSpec) -> Optional[Element]
    def wait_for(self, spec: ElementSpec, timeout: int) -> Element
    def register_strategy(self, strategy, finder_fn) -> None  # Extensible
```

### 6. MCP Tools

```python
# Available tools for Claude
tools = [
    "create_order",    # Create order (symbol, side, qty, type, price)
    "transmit_order",  # Send order
    "cancel_order",    # Cancel order(s)
    "search_symbol",   # Find and select symbol
    "open_chart",      # Open chart
    "get_portfolio",   # Get positions
    "get_position",    # Get specific position
    "screenshot",      # Capture screen (returns base64)
    "read_screen",     # OCR text from screen
    "get_status",      # Connection status
]
```

## Extension Points

### Adding New Action

```python
# 1. Create action class in actions/
class MyNewAction(Action):
    def validate(self, **kwargs) -> Optional[str]:
        # Validate parameters
        return None

    def execute(self, **kwargs) -> ActionResult:
        # Use self.keyboard, self.mouse, self.hotkeys, etc.
        self.hotkeys.search()
        self.keyboard.type_text("something")
        return ActionResult.ok("Done", data=result)

# 2. Register in ActionRegistry (actions/__init__.py)
class ActionRegistry:
    def __init__(self, toolkit):
        self._my_action = MyNewAction(toolkit)

    def my_action(self, **kwargs) -> ActionResult:
        return self._my_action.execute(**kwargs)

# 3. Add MCP tool (mcp_server/tools.py)
Tool(
    name="my_action",
    description="Does something",
    inputSchema={...}
)
```

### Adding New Hotkey

```python
# input/hotkeys.py
class NTWSAction(Enum):
    MY_ACTION = "my_action"

class NTWSHotkeys:
    DEFAULT_HOTKEYS = {
        NTWSAction.MY_ACTION: HotkeyBinding(
            NTWSAction.MY_ACTION, ['ctrl', 'shift'], 'm', 'My action'
        ),
    }
```

### Adding New Element Finding Strategy

```python
# core/element.py
class ElementFinder:
    def __init__(self, window):
        self._strategies[FindStrategy.MY_STRATEGY] = self._find_by_my_method

    def _find_by_my_method(self, spec: ElementSpec) -> Optional[Element]:
        # Custom finding logic
        pass
```

### Adding New Screen Region

```python
# screen/regions.py
class RegionManager:
    PREDEFINED_REGIONS = {
        'my_region': Region('my_region', 100, 200, 300, 50, 'Description'),
    }
```

## Data Flow

```
User Command
     ↓
NTWSToolkit.actions.create_order(...)
     ↓
CreateOrderAction.execute()
     ↓
├── self.hotkeys.search()      → Keyboard.hotkey('ctrl', 'f')
├── self.keyboard.type_text()  → pyautogui.typewrite()
├── self.hotkeys.buy()         → Keyboard.hotkey('alt', 'b')
└── ActionResult.ok()
     ↓
Result returned to user/MCP
```

## Safety Features

```python
@dataclass
class SafetyConfig:
    paper_trading_only: bool = True      # Require paper mode
    max_order_quantity: int = 1000       # Max shares per order
    max_order_value: float = 100000.0    # Max order value
    confirm_orders: bool = True          # Confirm before transmit
    fail_safe_enabled: bool = True       # PyAutoGUI corner abort
```

## Dependencies

```
pywinauto    - Windows UI Automation
pyautogui    - Keyboard/mouse simulation
easyocr      - Text recognition
Pillow       - Image processing
pywin32      - Windows API
mcp          - Claude MCP protocol
```

## Usage Example

```python
from ntws_automation import NTWSToolkit

toolkit = NTWSToolkit()
toolkit.connect()

# Via Python
result = toolkit.actions.create_order(
    symbol='AAPL',
    side='BUY',
    quantity=100,
    order_type='LMT',
    limit_price=150.00
)

# Via MCP (Claude calls this)
# Tool: create_order
# Args: {"symbol": "AAPL", "side": "BUY", "quantity": 100, ...}
```
