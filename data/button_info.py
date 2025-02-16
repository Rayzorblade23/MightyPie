# button_info.py

import logging
from copy import deepcopy
from typing import Dict, Any

from data.config import CONFIG
from utils.json_utils import JSONManager


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
            self.logger.info("Successfully loaded configuration.")
        else:
            self._initialize_tasks()
            self.logger.info("Config file not found. Initialized with default configuration.")

    def save_to_json(self) -> bool:
        """Save current configuration to JSON file atomically with error handling"""
        if not self.has_unsaved_changes:
            return True

        if JSONManager.save(self.program_name, self.button_config_filename, self.button_info_dict):
            self.has_unsaved_changes = False
            self.logger.info("Configuration saved successfully.")
            return True
        else:
            self.logger.error("Error saving configuration.")
            return False

    def update_button(self, index, update_dict):
        """Update a button's configuration (but don't save to file)"""
        try:
            # If the index doesn't exist, initialize it with default values
            if index not in self.button_info_dict:
                self.button_info_dict[index] = {
                    "task_type": "show_any_window",
                    "properties": {
                        "app_name": "",
                        "text_1": "",
                        "text_2": "",
                        "window_handle": -1,
                        "app_icon_path": "",
                        "exe_name": ""
                    }
                }

            # Update only the specified fields
            for key, value in update_dict.items():
                if isinstance(value, dict):
                    self.button_info_dict[index][key].update(value)
                else:
                    self.button_info_dict[index][key] = value

            # Verify the update hasn't broken the structure
            self._validate_button_config(self.button_info_dict[index])

            self.has_unsaved_changes = True

        except Exception as e:
            raise e

    def _validate_button_config(self, button_config):
        """Validate button configuration structure"""
        required_keys = {"task_type", "properties"}
        required_properties = {
            "app_name", "text_1", "text_2", "window_handle",
            "app_icon_path", "exe_name"
        }

        if not all(key in button_config for key in required_keys):
            raise ValueError("Missing required keys in button configuration")

        if not all(prop in button_config["properties"] for prop in required_properties):
            raise ValueError("Missing required properties in button configuration")

    def _initialize_tasks(self):
        """Initialize with default configuration"""
        # Pre-defined tasks (example data)
        self.button_info_dict = {
            4: {
                "task_type": "show_program_window",
                "properties": {
                    "app_name": "",
                    "app_icon_path": "",
                    "exe_name": "spotify.exe",
                    "exe_path": "",
                    "window_title": "Spotify Premium",
                    "window_handle": -1,
                }
            },
            24: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "toggle_maximize_window",
                }
            },
            25: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "restore_minimized_window",
                }
            },
            26: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "navigation_forward",
                }
            },
            27: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "focus_all_explorer_windows",
                }
            },
            28: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "minimize_window",
                }
            },
            29: {
                "task_type": "call_function",
                "properties": {
                    "function_name": "center_window",
                }
            },
            32: {
                "task_type": "launch_program",
                "properties": {
                    "app_name": "",
                    "app_icon_path": "",
                    "exe_name": "sourcetree.exe",
                    "exe_path": "",
                }
            },

        }

        # # Explorer reserved spaces
        # explorer_reserved_indexes = [8, 10, 12, 14]
        #
        # for i in explorer_reserved_indexes:
        #     if i not in self.button_info_dict:
        #         self.button_info_dict[i] = {
        #             "task_type": "show_any_window",
        #             "properties": {
        #                 "app_name": "Windows Explorer",
        #                 "text_1": "",
        #                 "text_2": "Windows Explorer",
        #                 "window_handle": -1,
        #                 "app_icon_path": "",
        #                 "exe_name": "explorer.exe"
        #             }
        #         }

        # Fill in missing tasks
        for i in range(CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU * (
                CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY + CONFIG.INTERNAL_NUM_PIE_MENUS_SECONDARY)):
            if i not in self.button_info_dict:
                self.button_info_dict[i] = {
                    "task_type": "show_any_window",
                    "properties": {
                        "app_name": "",
                        "app_icon_path": "",
                        "exe_name": "",
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
        """Filters tasks based on a given attribute and value, returning copies."""
        filtered: Dict[int, dict] = {}  # Dictionary to hold filtered tasks
        for task_id, task in self.button_info_dict.items():
            keys = attribute.split('.')
            temp = task
            try:
                for key in keys:
                    temp = temp[key]
                if temp == value:
                    filtered[task_id] = deepcopy(task)  # Use task_id as the key in the dictionary
            except KeyError:
                continue
        return filtered  # Now returns a dictionary of filtered tasks

    def get_all_tasks(self) -> Dict[int, Dict[str, Any]]:
        """Returns all tasks."""
        return self.button_info_dict

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of ButtonInfo."""
        return cls()
