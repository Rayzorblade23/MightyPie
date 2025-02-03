import json
import os
from dataclasses import dataclass, fields
from typing import Any, Tuple, List

from functions.color_functions import adjust_saturation
from json_utils import JSONManager  # Assuming the previous JSONManager is saved as json_utils.py

from dataclasses import dataclass
from typing import Tuple

@dataclass
class BaseConfig:
    """Base class with core, runtime, and UI configuration fields."""

    # Core configuration fields
    _PROGRAM_NAME: str = "MightyPie"
    _CACHE_FILENAME: str = "apps_info_cache.json"
    _BUTTON_CONFIG_FILENAME: str = "button_config.json"

    # Runtime configuration fields
    SHOW_SETTINGS_AT_STARTUP: bool = True
    REFRESH_INTERVAL: int = 3000
    TASKBAR_OPACITY: int = 150
    HOTKEY_OPEN_TASKS: str = "F14"
    HOTKEY_OPEN_WINCON: str = "F13"

    # Monitor and display settings
    SHOW_MONITOR_SECTION: bool = True
    MONITOR_SHORTCUT_1: Tuple[str, str] = ("win", "num1")
    MONITOR_SHORTCUT_2: Tuple[str, str] = ("win", "num2")
    MONITOR_SHORTCUT_3: Tuple[str, str] = ("win", "num3")

    # UI and layout configurations
    _MAX_BUTTONS: int = 8
    _NUM_PIE_TASK_SWITCHERS: int = 3
    _BUTTON_WIDTH: int = 140
    _BUTTON_HEIGHT: int = 34
    _CONTROL_BUTTON_SIZE: int = 30
    _CANVAS_SIZE: Tuple[int, int] = (800, 600)
    _RADIUS: int = 150
    _INNER_RADIUS: int = 18

    # Text and animation settings
    _PIE_TEXT_LABEL_MARGINS: int = 10
    _PIE_TEXT_LABEL_SCROLL_SPEED: int = 1
    _PIE_TEXT_LABEL_SCROLL_INTERVAL: int = 25

    # Color configurations
    ACCENT_COLOR: str = "#5a14b7"
    BG_COLOR: str = "#3b3b3b"


@dataclass
class ConfigManager(BaseConfig):
    """Manages application configuration with persistence and runtime editing."""

    def __post_init__(self):
        """Initialize configuration with JSON management."""
        # Load configuration using JSONManager
        loaded_config = JSONManager.load(
            app_name=self._PROGRAM_NAME,
            filename='app_settings.json',
            default=self._get_default_config()
        )

        # Update instance with loaded configuration
        self._update_from_dict(loaded_config)

        # Compute derived values
        self.ACCENT_COLOR_MUTED = adjust_saturation(self.ACCENT_COLOR, 0.5)

    def _get_config_directory(self) -> str:
        """Determine the appropriate configuration directory."""
        base_dirs = {
            "win32": os.path.join(os.environ.get('APPDATA', ''), self._PROGRAM_NAME),
            "darwin": os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', self._PROGRAM_NAME),
            "linux": os.path.join(os.path.expanduser('~'), '.config', self._PROGRAM_NAME)
        }
        return base_dirs.get(os.name, os.path.abspath('.'))

    def _get_default_config(self) -> dict:
        """Generate a default configuration dictionary."""
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
        }

    def _load_config(self):
        """Load configuration from JSON, with fallback to default values."""
        os.makedirs(self.config_dir, exist_ok=True)

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self._update_from_dict(loaded_config)
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")

    def _update_from_dict(self, config_dict: dict):
        """Update configuration from a dictionary, handling type conversions."""
        for field in fields(self):
            if field.name in config_dict:
                value = config_dict[field.name]
                try:
                    # Handle tuple conversions specifically
                    if field.type in (Tuple[str, str], Tuple[int, int]) and isinstance(value, list):
                        setattr(self, field.name, tuple(value))
                    else:
                        setattr(self, field.name, value)
                except Exception as e:
                    print(f"Could not set {field.name}: {e}")

    def save_config(self):
        """Save current configuration using JSONManager."""
        config_dict = {
            f.name: getattr(self, f.name)
            for f in fields(self)
        }

        JSONManager.save(
            app_name=self._PROGRAM_NAME,
            filename='app_settings.json',
            data=config_dict
        )

    def update_setting(self, setting: str, value: Any):
        """Update a single configuration setting."""
        if hasattr(self, setting):
            setattr(self, setting, value)

            # Special handling for derived values
            if setting == 'ACCENT_COLOR':
                self.ACCENT_COLOR_MUTED = adjust_saturation(value, 0.5)

            # Save updated configuration
            self.save_config()
        else:
            print(f"Setting {setting} not found.")

    def get_settings_for_ui(self) -> List[dict]:
        """Prepare settings for UI representation."""
        return [
            {
                "name": f.name,
                "value": getattr(self, f.name),
                "type": str(f.type)
            }
            for f in fields(self) if not f.name.startswith('_')
        ]


CONFIG = ConfigManager()

class DefaultConfig(BaseConfig):
    """Holds the default configuration values."""
    pass
