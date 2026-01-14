"""
Custom exceptions for NTWS automation.

Exception hierarchy:
    NTWSAutomationError (base)
    ├── WindowNotFoundError
    ├── ElementNotFoundError
    ├── TimeoutError
    ├── ActionFailedError
    └── OCRError
"""


class NTWSAutomationError(Exception):
    """
    Base exception for all NTWS automation errors.

    All custom exceptions inherit from this class,
    allowing catch-all error handling.
    """

    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class WindowNotFoundError(NTWSAutomationError):
    """
    NTWS window not found.

    Raised when:
    - NTWS is not running
    - Window title doesn't match expected pattern
    - Window is minimized/hidden and cannot be accessed
    """

    def __init__(self, message: str = "NTWS window not found", **kwargs):
        super().__init__(message, **kwargs)


class ElementNotFoundError(NTWSAutomationError):
    """
    UI element not found.

    Raised when element search fails via:
    - UI Automation tree
    - OCR text search
    - Image template matching
    """

    def __init__(self, element_spec: str = None, **kwargs):
        message = f"Element not found: {element_spec}" if element_spec else "Element not found"
        super().__init__(message, **kwargs)
        self.element_spec = element_spec


class TimeoutError(NTWSAutomationError):
    """
    Operation timed out.

    Raised when:
    - Wait for window exceeds timeout
    - Wait for element exceeds timeout
    - Action doesn't complete in expected time
    """

    def __init__(self, operation: str = None, timeout: float = None, **kwargs):
        message = f"Timeout waiting for: {operation}" if operation else "Operation timed out"
        if timeout:
            message += f" (timeout: {timeout}s)"
        super().__init__(message, **kwargs)
        self.operation = operation
        self.timeout = timeout


class ActionFailedError(NTWSAutomationError):
    """
    High-level action failed to complete.

    Raised when:
    - Order creation fails
    - Symbol search returns no results
    - Chart cannot be opened
    """

    def __init__(self, action: str = None, reason: str = None, **kwargs):
        message = f"Action failed: {action}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, **kwargs)
        self.action = action
        self.reason = reason


class OCRError(NTWSAutomationError):
    """
    OCR operation failed.

    Raised when:
    - OCR engine initialization fails
    - Text recognition fails
    - Expected text pattern not found
    """

    def __init__(self, message: str = "OCR operation failed", **kwargs):
        super().__init__(message, **kwargs)


class SafetyError(NTWSAutomationError):
    """
    Safety check failed.

    Raised when:
    - Live trading detected but paper trading required
    - Order quantity exceeds limit
    - Emergency stop triggered
    """

    def __init__(self, message: str = "Safety check failed", **kwargs):
        super().__init__(message, **kwargs)


class ConfigurationError(NTWSAutomationError):
    """
    Configuration error.

    Raised when:
    - Config file not found
    - Invalid config values
    - Missing required settings
    """

    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(message, **kwargs)
