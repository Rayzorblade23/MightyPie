# button_info.py

import logging
from copy import deepcopy
from typing import Dict, Any

from src.data.config import CONFIG
from src.utils.json_utils import JSONManager


class ButtonInfo:
    _instance = None  # Class-level variable for the singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False  # Prevent re-initialization
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return  # Skip re-initialization
        self.__initialized = True

        # Shorter variables for CONFIG.s...
        self.program_name = CONFIG.INTERNAL_PROGRAM_NAME
        self.button_config_filename = CONFIG.INTERNAL_BUTTON_CONFIG_FILENAME

        self.button_info_dict: Dict[int, Dict[str, Any]] = {}
        self.has_unsaved_changes = False

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.load_json()

    def load_json(self) -> None:
        """Load button configuration from JSON file with proper error handling"""
        loaded_dict = JSONManager.load(self.program_name, self.button_config_filename, default={})

        if loaded_dict:
            self.button_info_dict = {int(k): v for k, v in loaded_dict.items()}
        else:
            self._initialize_tasks()
            self.logger.info("Config file not found. Initialized with default configuration.")

    def save_to_json(self) -> bool:
        """Save current configuration to JSON file atomically with error handling"""
        if not self.has_unsaved_changes:
            return True

        if JSONManager.save(self.program_name, self.button_config_filename, self.button_info_dict):
            self.has_unsaved_changes = False
            return True
        else:
            self.logger.error("Error saving configuration.")
            return False

    def _initialize_button(self):
        """Initialize a button with empty configuration"""
        return {
            "task_type": "show_any_window",
            "properties": self.get_default_properties()
        }
    def update_button(self, index, update_dict):
        """Update a button's configuration (but don't save to file)"""
        try:
            # If the index doesn't exist, initialize it
            if index not in self.button_info_dict:
                self.button_info_dict[index] = self._initialize_button()

            task_type = update_dict.get("task_type", self.button_info_dict[index]["task_type"])

            # Update with complete property set first
            self.button_info_dict[index] = {
                "task_type": task_type,
                "properties": self.get_default_properties(task_type)
            }

            # Then overlay with any specific updates
            if "properties" in update_dict:
                self.button_info_dict[index]["properties"].update(update_dict["properties"])

            self._validate_button_config(self.button_info_dict[index])
            self.has_unsaved_changes = True

        except Exception as e:
            raise e

    @staticmethod
    def _validate_button_config(button_config):
        """Validate button configuration structure"""
        required_keys = {"task_type", "properties"}
        required_properties = {
            "show_any_window": {
                "app_name", "app_icon_path", "window_title",
                "window_handle", "exe_name"
            },
            "show_program_window": {
                "app_name", "app_icon_path", "exe_name", "exe_path",
                "window_title", "window_handle"
            },
            "launch_program": {
                "app_name", "app_icon_path", "exe_name", "exe_path"
            },
            "call_function": {"function_name"}
        }

        task_type = button_config.get("task_type", "show_any_window")
        if not all(key in button_config for key in required_keys):
            raise ValueError("Missing required keys in button configuration")

        if not all(prop in button_config["properties"] for prop in required_properties.get(task_type, [])):
            raise ValueError("Missing required properties in button configuration")

    def _initialize_tasks(self):
        """Initialize with default configuration"""
        # Pre-defined tasks (example data)
        self.button_info_dict = {
            0: {
                "task_type": "show_program_window",
                "properties": {
                    "app_name": "",
                    "app_icon_path": "",
                    "exe_name": "vivaldi.exe",
                    "exe_path": "",
                    "window_title": "",
                    "window_handle": -1
                }
            },
            4: {
                "task_type": "show_program_window",
                "properties": {
                    "app_name": "",
                    "app_icon_path": "",
                    "exe_name": "spotify.exe",
                    "exe_path": "",
                    "window_title": "",
                    "window_handle": -1
                }
            },
            8: {
                "task_type": "show_program_window",
                "properties": {
                    "app_name": "",
                    "app_icon_path": "",
                    "exe_name": "explorer.exe",
                    "exe_path": "",
                    "window_title": "",
                    "window_handle": -1
                }
            },
            10: {
                "task_type": "show_program_window",
                "properties": {
                    "app_name": "",
                    "app_icon_path": "",
                    "exe_name": "explorer.exe",
                    "exe_path": "",
                    "window_title": "",
                    "window_handle": -1
                }
            },
            12: {
                "task_type": "show_program_window",
                "properties": {
                    "app_name": "",
                    "app_icon_path": "",
                    "exe_name": "explorer.exe",
                    "exe_path": "",
                    "window_title": "",
                    "window_handle": -1
                }
            },
            14: {
                "task_type": "show_program_window",
                "properties": {
                    "app_name": "",
                    "app_icon_path": "",
                    "exe_name": "explorer.exe",
                    "exe_path": "",
                    "window_title": "",
                    "window_handle": -1
                }
            },
            24: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "toggle_maximize_window"
                }
            },
            25: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "restore_minimized_window"
                }
            },
            26: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "navigation_forward"
                }
            },
            27: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "focus_all_explorer_windows"
                }
            },
            28: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "minimize_window"
                }
            },
            29: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "center_window"
                }
            },
            30: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "navigation_backwards"
                }
            },
            31: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "clipboard"
                }
            },
            32: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "media_play_pause"
                }
            },
            33: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "media_skip_forward"
                }
            },
            34: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "paste"
                }
            },
            35: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "restart_explorer"
                }
            },
            36: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "media_mute"
                }
            },
            37: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "fullscreen_11"
                }
            },
            38: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "copy"
                }
            },
            39: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "media_skip_backward"
                }
            },
        }

        total_entries = CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU * (
                CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY + CONFIG.INTERNAL_NUM_PIE_MENUS_SECONDARY)

        # fill last pie menu with launchers
        for i in range(total_entries - 8, total_entries):
            if i not in self.button_info_dict:
                self.button_info_dict[i] = {
                    "task_type": "launch_program",
                    "properties": {
                        "app_name": "",
                        "app_icon_path": "",
                        "exe_name": "explorer.exe",
                        "exe_path": "",
                        "window_title": ""
                    }
                }

        # Fill in missing tasks
        for i in range(total_entries):
            if i not in self.button_info_dict:
                self.button_info_dict[i] = {
                    "task_type": "show_any_window",
                    "properties": {
                        "app_name": "",
                        "app_icon_path": "",
                        "window_title": "",
                        "window_handle": -1,
                    }
                }

        # Save the initial configuration
        self.save_to_json()

    def __getitem__(self, index):
        """Allow direct access to tasks via index like task[index]."""
        return self.button_info_dict.get(index, None)

    def __setitem__(self, index, value):
        """Allow setting values directly and save to JSON"""
        self.button_info_dict[index] = value
        self.save_to_json()

    def __iter__(self):
        """Allow iteration over the keys of button_info_dict."""
        return iter(self.button_info_dict)

    def get_button_info_list(self) -> list:
        """Returns the button info as a sorted list of dictionaries by index."""
        # Sort the button_info_dict by the keys (index)
        sorted_button_info = sorted(self.button_info_dict.items(), key=lambda item: item[0])
        return [value for key, value in sorted_button_info]

    def items(self):
        """Allow direct access to items like button_info.items()."""
        return self.button_info_dict.items()

    def keys(self):
        """Allow direct access to keys like button_info.keys()."""
        return self.button_info_dict.keys()

    def values(self):
        """Allow direct access to values like button_info.values()."""
        return self.button_info_dict.values()

    def get_task_indexes(self):
        """Returns a list of all task indexes."""
        return list(self.button_info_dict.keys())

    def filter_buttons(self, attribute: str, value: str) -> Dict[int, dict]:
        """Filters tasks based on a given attribute and value, returning a deep copy of both dict and contents."""
        filtered = {
            task_id: task
            for task_id, task in self.button_info_dict.items()
            if task.get(attribute) == value
        }
        return deepcopy(filtered)  # Deep copy the entire filtered dictionary

    def get_all_tasks(self) -> Dict[int, Dict[str, Any]]:
        """Returns all tasks."""
        return self.button_info_dict

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of ButtonInfo."""
        return cls()

    @classmethod
    def get_default_properties(cls, task_type: str = "show_any_window") -> dict:
        """Returns the default properties for a given task type."""
        properties = {
            "show_any_window": {
                "app_name": "",
                "app_icon_path": "",
                "window_title": "",
                "window_handle": -1,
                "exe_name": "explorer.exe",
                "exe_path": ""
            },
            "show_program_window": {
                "app_name": "",
                "app_icon_path": "",
                "exe_name": "explorer.exe",
                "exe_path": "",
                "window_title": "",
                "window_handle": -1
            },
            "launch_program": {
                "app_name": "",
                "app_icon_path": "",
                "exe_name": "explorer.exe",
                "exe_path": ""
            },
            "call_function": {
                "function_name": "toggle_maximize_window"
            }
        }
        return properties.get(task_type, properties["show_any_window"]).copy()