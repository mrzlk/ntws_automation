"""
Configuration management for TWS automation toolkit.

Provides dataclass-based configuration with:
- File persistence (YAML)
- Environment variable overrides
- Sensible defaults
- Validation
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScreenConfig:
    """Screen/display configuration."""
    base_resolution: tuple = (1920, 1080)
    current_resolution: Optional[tuple] = None
    scale_factor: float = 1.0
    dpi_aware: bool = True


@dataclass
class TimingConfig:
    """Timing and delay configuration."""
    action_delay: float = 0.1
    typing_interval: float = 0.02
    element_timeout: int = 10
    window_timeout: int = 30
    ocr_timeout: int = 5
    retry_delay: float = 1.0
    max_retries: int = 3


@dataclass
class OCRConfig:
    """OCR configuration."""
    engine: str = 'easyocr'  # 'easyocr' or 'tesseract'
    languages: List[str] = field(default_factory=lambda: ['en'])
    use_gpu: bool = True
    confidence_threshold: float = 0.5
    model_path: Optional[str] = None


@dataclass
class SafetyConfig:
    """
    Safety configuration.

    IMPORTANT: These settings help prevent accidental
    trading actions. Modify with caution.
    """
    paper_trading_only: bool = True
    max_order_quantity: int = 1000
    max_order_value: float = 100000.0
    confirm_orders: bool = True
    fail_safe_enabled: bool = True
    emergency_stop_corners: bool = True
    log_all_actions: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = 'INFO'
    file_path: Optional[str] = None
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    max_bytes: int = 10_000_000
    backup_count: int = 5
    console_output: bool = True


@dataclass
class ToolkitConfig:
    """
    Main toolkit configuration.

    Contains all sub-configurations for the automation toolkit.
    """
    tws_path: str = r'C:\Jts'
    screen: ScreenConfig = field(default_factory=ScreenConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    custom_regions: Dict[str, Any] = field(default_factory=dict)
    custom_hotkeys: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """
    Configuration manager with file persistence.

    Handles loading, saving, and accessing configuration.
    Supports YAML format with environment variable overrides.

    Attributes:
        DEFAULT_CONFIG_PATH: Default location for config file.
    """

    DEFAULT_CONFIG_PATH = Path.home() / '.tws_automation' / 'config.yaml'

    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Optional path to config file.
                        Uses default if not specified.
        """
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self.config = ToolkitConfig()
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            logger.info(f"Config file not found, using defaults: {self.config_path}")
            return

        try:
            import yaml

            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f) or {}

            self._apply_config(data)
            logger.info(f"Loaded config from {self.config_path}")

        except ImportError:
            logger.warning("PyYAML not installed, using defaults")
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def _apply_config(self, data: dict) -> None:
        """Apply loaded config data to config object."""
        if 'tws_path' in data:
            self.config.tws_path = data['tws_path']

        if 'screen' in data:
            self._update_dataclass(self.config.screen, data['screen'])

        if 'timing' in data:
            self._update_dataclass(self.config.timing, data['timing'])

        if 'ocr' in data:
            self._update_dataclass(self.config.ocr, data['ocr'])

        if 'safety' in data:
            self._update_dataclass(self.config.safety, data['safety'])

        if 'logging' in data:
            self._update_dataclass(self.config.logging, data['logging'])

        if 'custom_regions' in data:
            self.config.custom_regions = data['custom_regions']

        if 'custom_hotkeys' in data:
            self.config.custom_hotkeys = data['custom_hotkeys']

    def _update_dataclass(self, obj: Any, data: dict) -> None:
        """Update dataclass fields from dictionary."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

    def save(self) -> None:
        """Save configuration to file."""
        try:
            import yaml

            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict
            data = self._config_to_dict()

            with open(self.config_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Saved config to {self.config_path}")

        except ImportError:
            logger.error("PyYAML not installed, cannot save config")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def _config_to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            'tws_path': self.config.tws_path,
            'screen': asdict(self.config.screen),
            'timing': asdict(self.config.timing),
            'ocr': asdict(self.config.ocr),
            'safety': asdict(self.config.safety),
            'logging': asdict(self.config.logging),
            'custom_regions': self.config.custom_regions,
            'custom_hotkeys': self.config.custom_hotkeys,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.

        Args:
            key: Config key (e.g., 'safety.paper_trading_only').
            default: Default value if key not found.

        Returns:
            Config value or default.
        """
        parts = key.split('.')
        obj = self.config

        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return default

        return obj

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Config key (e.g., 'timing.action_delay').
            value: Value to set.
        """
        parts = key.split('.')
        obj = self.config

        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                raise KeyError(f"Invalid config key: {key}")

        if hasattr(obj, parts[-1]):
            setattr(obj, parts[-1], value)
        else:
            raise KeyError(f"Invalid config key: {key}")

    def reset(self) -> None:
        """Reset to default configuration."""
        self.config = ToolkitConfig()
        logger.info("Config reset to defaults")

    def validate(self) -> List[str]:
        """
        Validate configuration.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Check TWS path
        if not Path(self.config.tws_path).exists():
            errors.append(f"TWS path not found: {self.config.tws_path}")

        # Check timing values
        if self.config.timing.action_delay < 0:
            errors.append("action_delay must be non-negative")

        if self.config.timing.element_timeout <= 0:
            errors.append("element_timeout must be positive")

        # Check safety values
        if self.config.safety.max_order_quantity <= 0:
            errors.append("max_order_quantity must be positive")

        # Check OCR engine
        if self.config.ocr.engine not in ('easyocr', 'tesseract'):
            errors.append(f"Invalid OCR engine: {self.config.ocr.engine}")

        return errors

    def __repr__(self) -> str:
        return f"ConfigManager(path={self.config_path})"
