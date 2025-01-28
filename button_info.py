# button_info.py

import json
import os
import shutil
import tempfile



from config import CONFIG


class ButtonInfo:
    def __init__(self):
        self.button_info_dict = {}
        self.has_unsaved_changes = False

        self.load_json()

    def load_json(self):
        # Try to load from JSON first, fall back to default initialization
        if os.path.exists(CONFIG.BUTTON_CONFIG_FILENAME):
            try:
                with open(CONFIG.BUTTON_CONFIG_FILENAME, 'r') as f:
                    loaded_dict = json.load(f)
                    # Convert string keys back to integers
                    self.button_info_dict = {int(k): v for k, v in loaded_dict.items()}
            except Exception:
                self._initialize_tasks()
        else:
            self._initialize_tasks()

    def save_to_json(self):
        """Save current configuration to JSON file atomically"""
        if not self.has_unsaved_changes:
            return  # Skip saving if no changes were made

        # Create a temporary file in the same directory as the target file
        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(CONFIG.BUTTON_CONFIG_FILENAME)))
        try:
            with os.fdopen(temp_fd, 'w') as temp_file:
                # Write the new content to the temporary file
                json.dump(self.button_info_dict, temp_file, indent=4)
                # Ensure all data is written to disk
                temp_file.flush()
                os.fsync(temp_fd)

            # Atomic replace of the old file with the new file
            if os.name == 'nt':  # Windows
                if os.path.exists(CONFIG.BUTTON_CONFIG_FILENAME):
                    os.remove(CONFIG.BUTTON_CONFIG_FILENAME)
            shutil.move(temp_path, CONFIG.BUTTON_CONFIG_FILENAME)

            self.has_unsaved_changes = False

        except Exception as e:
            # Clean up the temporary file if something goes wrong
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

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


