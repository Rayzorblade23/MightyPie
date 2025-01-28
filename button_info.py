import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

from config import CONFIG


class ButtonInfo:
    def __init__(self):
        self.button_info_dict: Dict[int, Dict[str, Any]] = {}
        self.has_unsaved_changes = False

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.load_json()

    def get_config_dir(self) -> str:
        """Get the appropriate configuration directory based on runtime environment"""
        if hasattr(sys, '_MEIPASS'):  # Running as compiled executable
            if sys.platform == "win32":
                return os.path.join(os.environ.get('APPDATA'), CONFIG.PROGRAM_NAME)
            elif sys.platform == "darwin":
                return os.path.join(str(Path.home()), "Library", "Application Support", CONFIG.PROGRAM_NAME)
            else:  # Linux and other Unix
                return os.path.join(str(Path.home()), ".config", CONFIG.PROGRAM_NAME)
        else:  # Running as script
            return os.path.abspath(".")

    def get_config_file(self) -> str:
        """Get the full path to the configuration file"""
        config_dir = self.get_config_dir()
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, CONFIG.BUTTON_CONFIG_FILENAME)

    def load_json(self) -> None:
        """Load button configuration from JSON file with proper error handling"""
        config_file = self.get_config_file()
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_dict = json.load(f)
                    self.button_info_dict = {int(k): v for k, v in loaded_dict.items()}
                    self.logger.info(f"Successfully loaded configuration from {config_file}")
            else:
                self._initialize_tasks()
                self.logger.info("Config file not found. Initialized with default configuration")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON from {config_file}: {e}")
            self._initialize_tasks()
        except Exception as e:
            self.logger.error(f"Unexpected error loading config: {e}")
            self._initialize_tasks()

    def save_to_json(self) -> bool:
        """Save current configuration to JSON file atomically with error handling"""
        if not self.has_unsaved_changes:
            return True

        config_file = self.get_config_file()
        temp_file_path = None

        try:
            # Create temporary file in the same directory
            with tempfile.NamedTemporaryFile('w', delete=False, dir=os.path.dirname(config_file)) as temp_file:
                json.dump(self.button_info_dict, temp_file, indent=4)
                temp_file_path = temp_file.name

            # Atomic replace
            if os.path.exists(config_file):
                os.remove(config_file)
            os.rename(temp_file_path, config_file)

            self.has_unsaved_changes = False
            self.logger.info("Configuration saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            # Cleanup: Remove the temporary file if it exists
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
            return False

    # Rest of the ButtonInfo class methods remain the same...

    def update_button(self, index, update_dict):
        """Update a button's configuration (but don't save to file)"""
        try:
            # If the index doesn't exist, initialize it with default values
            if index not in self.button_info_dict:
                self.button_info_dict[index] = {
                    "task_type": "program_window_any",
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
            0: {
                "task_type": "program_window_fixed",
                "properties": {
                    "app_name": "Vivaldi",
                    "text_1": "",
                    "text_2": "",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": "vivaldi.exe"
                }
            },
            4: {
                "task_type": "program_window_fixed",
                "properties": {
                    "app_name": "Spotify",
                    "text_1": "",
                    "text_2": "",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": "spotify.exe"
                }
            },
            6: {
                "task_type": "program_window_fixed",
                "properties": {
                    "app_name": "Telegram Desktop",
                    "text_1": "",
                    "text_2": "Telegram Desktop",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": "telegram.exe"
                }
            }
        }

        # Explorer reserved spaces
        explorer_reserved_indexes = [8, 10, 12, 14]

        for i in explorer_reserved_indexes:
            if i not in self.button_info_dict:
                self.button_info_dict[i] = {
                    "task_type": "program_window_fixed",
                    "properties": {
                        "app_name": "Windows Explorer",
                        "text_1": "",
                        "text_2": "Windows Explorer",
                        "window_handle": -1,
                        "app_icon_path": "",
                        "exe_name": "explorer.exe"
                    }
                }

        # Fill in missing tasks
        for i in range(CONFIG.MAX_BUTTONS * CONFIG.NUM_PIE_TASK_SWITCHERS):
            if i not in self.button_info_dict:
                self.button_info_dict[i] = {
                    "task_type": "program_window_any",
                    "properties": {
                        "app_name": "",
                        "text_1": "",
                        "text_2": "",
                        "window_handle": -1,
                        "app_icon_path": "",
                        "exe_name": ""
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

    def filter_buttons(self, attribute, value):
        """
        Filters tasks based on a given attribute and value.

        :param attribute: Attribute to check (can be nested, e.g., 'properties.text_2')
        :param value: The value to match
        :return: A list of tasks matching the criteria
        """
        filtered = []
        for task_id, task in self.button_info_dict.items():
            keys = attribute.split('.')
            temp = task
            try:
                for key in keys:
                    temp = temp[key]
                if temp == value:
                    filtered.append(task)
            except KeyError:
                continue
        return filtered

    def get_all_tasks(self):
        """Returns all tasks."""
        return self.button_info_dict
