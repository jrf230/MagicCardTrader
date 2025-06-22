"""Configuration management for MTG Buylist Aggregator."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "use_mock": False,
    "collection_file": "collection.csv",
    "output_format": "table",
    "track_history": True,
    "show_trends": True,
    "history_file": "price_history.json",
    "log_level": "INFO",
    "vendor_timeout": 10,
    "max_retries": 2,
    "export_dir": ".",
    "currency": "USD",
    "risk_tolerance": "medium",
    "recommendation_days": 7,
    "analytics_days": 30,
    "hot_card_days": 7,
    "min_price_threshold": 0.01,
    "max_cards": 1000,
    "user_id": None,
    "multi_user": False,
}


class Config:
    """Manages application configuration."""

    DEFAULT_CONFIG = DEFAULT_CONFIG

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        home = Path.home()
        return home / ".mtg_buylist_config.json"

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file, creating default if not exists."""
        config = self.DEFAULT_CONFIG.copy()

        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    file_config = json.load(f)
                config.update(file_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
        else:
            # Create default config file
            try:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_path, "w") as f:
                    json.dump(config, f, indent=2)
                logger.info(f"Created default configuration at {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to create config file: {e}")

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value, interpreting 'true'/'false' as booleans."""
        value = self.config.get(key, default)
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            if value.lower() == "false":
                return False
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config[key] = value

    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def merge_cli_args(self, args: Dict[str, Any]) -> None:
        """Merge CLI arguments with config (CLI takes precedence)."""
        for key, value in args.items():
            if value is not None:  # Only override if CLI provided a value
                self.config[key] = value

    def get_vendor_list(self) -> list:
        """Get list of preferred vendors."""
        return self.config.get("preferred_vendors", [])

    def is_mock_mode(self) -> bool:
        """Check if mock mode is enabled (handles string/boolean)."""
        value = self.get("use_mock", True)
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)

    def get_collection_file(self) -> str:
        """Get the collection file path."""
        return self.config.get("collection_file", "collection.csv")

    def get_output_format(self) -> str:
        """Get the output format preference."""
        return self.config.get("output_format", "pretty")
