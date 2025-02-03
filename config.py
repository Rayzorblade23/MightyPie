import json
import os
from dataclasses import dataclass, fields
from typing import Any, Tuple, List

from functions.color_functions import adjust_saturation
from json_utils import JSONManager  # Assuming the previous JSONManager is saved as json_utils.py


# Shared configuration constants
DEFAULT_CONFIG = {
    "PROGRAM_NAME": "MightyPie",
    "CACHE_FILENAME": "apps_info_cache.json",
    "BUTTON_CONFIG_FILENAME": "button_config.json",
    "REFRESH_INTERVAL": 3000,
    "TASKBAR_OPACITY": 150,
    "HOTKEY_OPEN_TASKS": "F14",
    "HOTKEY_OPEN_WINCON": "F13",
    "SHOW_MONITOR_SECTION": True,
    "MONITOR_SHORTCUT_1": ("win", "num1"),
    "MONITOR_SHORTCUT_2": ("win", "num2"),
    "MONITOR_SHORTCUT_3": ("win", "num3"),
    "MAX_BUTTONS": 8,
    "NUM_PIE_TASK_SWITCHERS": 3,
    "BUTTON_WIDTH": 140,
    "BUTTON_HEIGHT": 34,
    "CONTROL_BUTTON_SIZE": 30,
    "CANVAS_SIZE": (800, 600),
    "RADIUS": 150,
    "INNER_RADIUS": 18,
    "PIE_TEXT_LABEL_MARGINS": 10,
    "PIE_TEXT_LABEL_SCROLL_SPEED": 1,
    "PIE_TEXT_LABEL_SCROLL_INTERVAL": 25,
    "ACCENT_COLOR": "#5a14b7",
    "BG_COLOR": "#3b3b3b",
}


@dataclass
class ConfigBase:
    """Base configuration for managing application settings with persistence and runtime editing."""

    # Core configuration fields
    PROGRAM_NAME: str = DEFAULT_CONFIG["PROGRAM_NAME"]
    CACHE_FILENAME: str = DEFAULT_CONFIG["CACHE_FILENAME"]
    BUTTON_CONFIG_FILENAME: str = DEFAULT_CONFIG["BUTTON_CONFIG_FILENAME"]

    # Runtime configuration fields
    REFRESH_INTERVAL: int = DEFAULT_CONFIG["REFRESH_INTERVAL"]
    TASKBAR_OPACITY: int = DEFAULT_CONFIG["TASKBAR_OPACITY"]
    HOTKEY_OPEN_TASKS: str = DEFAULT_CONFIG["HOTKEY_OPEN_TASKS"]
    HOTKEY_OPEN_WINCON: str = DEFAULT_CONFIG["HOTKEY_OPEN_WINCON"]

    # Monitor and display settings
    SHOW_MONITOR_SECTION: bool = DEFAULT_CONFIG["SHOW_MONITOR_SECTION"]
    MONITOR_SHORTCUT_1: Tuple[str, str] = DEFAULT_CONFIG["MONITOR_SHORTCUT_1"]
    MONITOR_SHORTCUT_2: Tuple[str, str] = DEFAULT_CONFIG["MONITOR_SHORTCUT_2"]
    MONITOR_SHORTCUT_3: Tuple[str, str] = DEFAULT_CONFIG["MONITOR_SHORTCUT_3"]

    # UI and layout configurations
    MAX_BUTTONS: int = DEFAULT_CONFIG["MAX_BUTTONS"]
    NUM_PIE_TASK_SWITCHERS: int = DEFAULT_CONFIG["NUM_PIE_TASK_SWITCHERS"]
    BUTTON_WIDTH: int = DEFAULT_CONFIG["BUTTON_WIDTH"]
    BUTTON_HEIGHT: int = DEFAULT_CONFIG["BUTTON_HEIGHT"]
    CONTROL_BUTTON_SIZE: int = DEFAULT_CONFIG["CONTROL_BUTTON_SIZE"]
    CANVAS_SIZE: Tuple[int, int] = DEFAULT_CONFIG["CANVAS_SIZE"]
    RADIUS: int = DEFAULT_CONFIG["RADIUS"]
    INNER_RADIUS: int = DEFAULT_CONFIG["INNER_RADIUS"]

    # Text and animation settings
    PIE_TEXT_LABEL_MARGINS: int = DEFAULT_CONFIG["PIE_TEXT_LABEL_MARGINS"]
    PIE_TEXT_LABEL_SCROLL_SPEED: int = DEFAULT_CONFIG["PIE_TEXT_LABEL_SCROLL_SPEED"]
    PIE_TEXT_LABEL_SCROLL_INTERVAL: int = DEFAULT_CONFIG["PIE_TEXT_LABEL_SCROLL_INTERVAL"]

    # Color configurations
    ACCENT_COLOR: str = DEFAULT_CONFIG["ACCENT_COLOR"]
    BG_COLOR: str = DEFAULT_CONFIG["BG_COLOR"]

    def __post_init__(self):
        """Initialize configuration with JSON management."""
        loaded_config = JSONManager.load(
            app_name=self.PROGRAM_NAME,
            filename='app_settings.json',
            default=self._get_default_config()
        )
        self._update_from_dict(loaded_config)
        self.ACCENT_COLOR_MUTED = adjust_saturation(self.ACCENT_COLOR, 0.5)

    def _get_default_config(self) -> dict:
        """Generate a default configuration dictionary."""
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def _update_from_dict(self, config_dict: dict):
        """Update configuration from a dictionary, handling type conversions."""
        for field in fields(self):
            if field.name in config_dict:
                value = config_dict[field.name]
                try:
                    if field.type in (Tuple[str, str], Tuple[int, int]) and isinstance(value, list):
                        setattr(self, field.name, tuple(value))
                    else:
                        setattr(self, field.name, value)
                except Exception as e:
                    print(f"Could not set {field.name}: {e}")

    def save_config(self):
        """Save current configuration using JSONManager."""
        config_dict = {f.name: getattr(self, f.name) for f in fields(self)}
        JSONManager.save(
            app_name=self.PROGRAM_NAME,
            filename='app_settings.json',
            data=config_dict
        )

    def update_setting(self, setting: str, value: Any):
        """Update a single configuration setting."""
        if hasattr(self, setting):
            setattr(self, setting, value)
            if setting == 'ACCENT_COLOR':
                self.ACCENT_COLOR_MUTED = adjust_saturation(value, 0.5)
            self.save_config()
        else:
            print(f"Setting {setting} not found.")

    def get_settings_for_ui(self) -> List[dict]:
        """Prepare settings for UI representation."""
        return [
            {"name": f.name, "value": getattr(self, f.name), "type": str(f.type)}
            for f in fields(self) if not f.name.startswith('_')
        ]


# ConfigManager now extends ConfigBase to avoid duplication
@dataclass
class ConfigManager(ConfigBase):
    pass


CONFIG = ConfigManager()

# TaskPieSwitcherConfig can also extend ConfigBase
@dataclass
class TaskPieSwitcherConfig(ConfigBase):
    pass
