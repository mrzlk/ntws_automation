"""
Logging configuration for TWS automation toolkit.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

_loggers: Dict[str, logging.Logger] = {}
_initialized = False


def setup_logging(config: 'LoggingConfig') -> None:
    """
    Setup logging based on configuration.

    Args:
        config: LoggingConfig instance.
    """
    global _initialized

    if _initialized:
        return

    # Get root logger for tws_automation
    root_logger = logging.getLogger('tws_automation')
    root_logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(config.format)

    # Console handler
    if config.console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if config.file_path:
        log_path = Path(config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get or create logger for module.

    Args:
        name: Logger name (will be prefixed with tws_automation).

    Returns:
        Logger instance.
    """
    full_name = f'tws_automation.{name}'

    if full_name not in _loggers:
        _loggers[full_name] = logging.getLogger(full_name)

    return _loggers[full_name]


class ActionLogger:
    """
    Logger that records all automation actions.

    Provides structured logging of actions for:
    - Debugging
    - Audit trail
    - Replay/analysis
    """

    def __init__(self, log_path: str = None):
        """
        Initialize action logger.

        Args:
            log_path: Path to action log file.
        """
        self.log_path = log_path
        self.actions: List[Dict[str, Any]] = []
        self._logger = get_logger('ActionLogger')

    def log_action(
        self,
        action_name: str,
        params: dict,
        result: Any,
        duration: float
    ) -> None:
        """
        Log an action execution.

        Args:
            action_name: Name of the action.
            params: Action parameters.
            result: Action result.
            duration: Execution time in seconds.
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action_name,
            'params': params,
            'result': str(result),
            'success': getattr(result, 'success', None),
            'duration': duration
        }

        self.actions.append(entry)
        self._logger.debug(f"Action: {action_name} ({duration:.3f}s)")

        # Write to file if path specified
        if self.log_path:
            self._write_entry(entry)

    def _write_entry(self, entry: dict) -> None:
        """Write single entry to log file."""
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            self._logger.error(f"Failed to write action log: {e}")

    def export(self, path: str) -> None:
        """
        Export action log to file.

        Args:
            path: Output file path.
        """
        try:
            with open(path, 'w') as f:
                json.dump(self.actions, f, indent=2)
            self._logger.info(f"Exported {len(self.actions)} actions to {path}")
        except Exception as e:
            self._logger.error(f"Failed to export action log: {e}")

    def clear(self) -> None:
        """Clear in-memory action log."""
        self.actions.clear()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of logged actions.

        Returns:
            Summary dictionary with counts and timing.
        """
        if not self.actions:
            return {'total': 0}

        successful = sum(1 for a in self.actions if a.get('success'))
        failed = sum(1 for a in self.actions if a.get('success') is False)
        total_duration = sum(a.get('duration', 0) for a in self.actions)

        return {
            'total': len(self.actions),
            'successful': successful,
            'failed': failed,
            'total_duration': total_duration,
            'avg_duration': total_duration / len(self.actions)
        }
