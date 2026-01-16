"""
Base classes for high-level TWS actions.

Provides:
- Abstract Action base class
- ActionResult for standardized responses
- CompositeAction for action sequences
- Retry and logging decorators
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, TYPE_CHECKING
import logging
import time

if TYPE_CHECKING:
    from .. import TWSToolkit

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """
    Standardized action result.

    Attributes:
        success: Whether action completed successfully.
        message: Human-readable result message.
        data: Optional result data (varies by action).
        error: Error message if failed.
        duration: Action execution time in seconds.
    """
    success: bool
    message: str = ""
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, message: str = "Success", data: Any = None, **kwargs) -> 'ActionResult':
        """Create successful result."""
        return cls(success=True, message=message, data=data, **kwargs)

    @classmethod
    def fail(cls, error: str, message: str = "Failed", **kwargs) -> 'ActionResult':
        """Create failed result."""
        return cls(success=False, message=message, error=error, **kwargs)


class Action(ABC):
    """
    Base class for all TWS actions.

    Actions are high-level operations that combine
    low-level automation primitives (keyboard, mouse, OCR)
    to accomplish trading tasks.

    Subclasses must implement:
    - execute(**kwargs): Perform the action
    - validate(**kwargs): Validate parameters

    Attributes:
        toolkit: Reference to TWSToolkit for accessing components.
    """

    def __init__(self, toolkit: 'TWSToolkit'):
        """
        Initialize action.

        Args:
            toolkit: Parent TWSToolkit instance.
        """
        self.toolkit = toolkit
        self._logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    # Convenience accessors

    @property
    def window(self):
        """Get TWS window manager."""
        return self.toolkit.window

    @property
    def keyboard(self):
        """Get keyboard automation."""
        return self.toolkit.keyboard

    @property
    def mouse(self):
        """Get mouse automation."""
        return self.toolkit.mouse

    @property
    def hotkeys(self):
        """Get TWS hotkey manager."""
        return self.toolkit.hotkeys

    @property
    def ocr(self):
        """Get OCR engine."""
        return self.toolkit.ocr

    @property
    def capture(self):
        """Get screen capture."""
        return self.toolkit.capture

    @property
    def finder(self):
        """Get element finder."""
        return self.toolkit.finder

    @property
    def config(self):
        """Get toolkit configuration."""
        return self.toolkit.config

    @abstractmethod
    def execute(self, **kwargs) -> ActionResult:
        """
        Execute the action.

        Args:
            **kwargs: Action-specific parameters.

        Returns:
            ActionResult indicating success/failure.
        """
        pass

    def validate(self, **kwargs) -> Optional[str]:
        """
        Validate action parameters.

        Override in subclasses for custom validation.

        Args:
            **kwargs: Parameters to validate.

        Returns:
            Error message if invalid, None if valid.
        """
        return None

    def _wait_for_ready(self, timeout: int = None) -> bool:
        """
        Wait for TWS to be ready.

        Args:
            timeout: Maximum wait time.

        Returns:
            True if ready, False if timeout.
        """
        timeout = timeout or self.config.timing.window_timeout
        start = time.time()

        while time.time() - start < timeout:
            if self.window.is_ready():
                return True
            time.sleep(0.5)

        return False

    def _delay(self, seconds: float = None) -> None:
        """
        Pause execution.

        Args:
            seconds: Delay duration (uses config default if None).
        """
        seconds = seconds or self.config.timing.action_delay
        time.sleep(seconds)

    def _log_action(self, action: str, params: dict = None) -> None:
        """Log action execution."""
        if self.config.safety.log_all_actions:
            self._logger.info(f"Executing: {action} {params or ''}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class CompositeAction(Action):
    """
    Action composed of multiple sub-actions.

    Executes a sequence of actions, optionally
    stopping on first failure.

    Attributes:
        actions: List of actions to execute.
        stop_on_failure: If True, stop on first failed action.
    """

    def __init__(
        self,
        toolkit: 'TWSToolkit',
        actions: List[Action] = None,
        stop_on_failure: bool = True
    ):
        """
        Initialize composite action.

        Args:
            toolkit: Parent toolkit.
            actions: Initial list of actions.
            stop_on_failure: Stop if any action fails.
        """
        super().__init__(toolkit)
        self.actions = actions or []
        self.stop_on_failure = stop_on_failure

    def add(self, action: Action) -> 'CompositeAction':
        """
        Add action to sequence.

        Args:
            action: Action to add.

        Returns:
            Self for chaining.
        """
        self.actions.append(action)
        return self

    def execute(self, **kwargs) -> ActionResult:
        """
        Execute all actions in sequence.

        Args:
            **kwargs: Passed to each action.

        Returns:
            ActionResult with list of sub-results in data.
        """
        results = []
        start_time = time.time()

        for action in self.actions:
            result = action.execute(**kwargs)
            results.append(result)

            if not result.success and self.stop_on_failure:
                return ActionResult.fail(
                    error=f"Action failed: {action}",
                    message="Composite action stopped on failure",
                    data=results,
                    duration=time.time() - start_time
                )

        return ActionResult.ok(
            message=f"Completed {len(self.actions)} actions",
            data=results,
            duration=time.time() - start_time
        )

    def validate(self, **kwargs) -> Optional[str]:
        """Validate all sub-actions."""
        for action in self.actions:
            error = action.validate(**kwargs)
            if error:
                return f"{action}: {error}"
        return None
