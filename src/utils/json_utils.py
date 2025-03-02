import os
import json
import tempfile
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class JSONManager:
    @staticmethod
    def get_config_directory(app_name: str, config_type: str = 'config') -> str:
        """Get the appropriate configuration directory based on runtime environment and platform."""
        if hasattr(sys, '_MEIPASS'):  # Running as compiled executable
            if sys.platform == "win32":
                base_dir = os.environ.get('APPDATA', '')
            elif sys.platform == "darwin":
                base_dir = os.path.join(str(Path.home()), "Library", "Application Support")
            else:  # Linux and other Unix
                base_dir = os.path.join(str(Path.home()), ".config" if config_type == 'config' else ".cache")
        else:  # Running as script
            base_dir = ""

        config_path = os.path.join(base_dir, app_name)
        os.makedirs(config_path, exist_ok=True)
        return config_path

    @classmethod
    def load(cls, app_name: str, filename: str, default: Optional[Dict[Any, Any]] = None) -> Dict[Any, Any]:
        """
        Load JSON data from a file with robust error handling.

        :param app_name: Name of the application
        :param filename: Name of the JSON file
        :param default: Default dictionary to return if loading fails
        :return: Loaded dictionary or default
        """
        config_dir = cls.get_config_directory(app_name)
        filepath = os.path.join(config_dir, filename)

        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif default is not None:
                return default
            return {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading {filename}: {e}")
            return default or {}

    @classmethod
    def save(cls, app_name: str, filename: str, data: Dict[Any, Any]) -> bool:
        """
        Save data to a JSON file atomically.

        :param app_name: Name of the application
        :param filename: Name of the JSON file
        :param data: Dictionary to save
        :return: Boolean indicating success
        """
        config_dir = cls.get_config_directory(app_name)
        filepath = os.path.join(config_dir, filename)

        try:
            # Create a temporary file in the same directory
            with tempfile.NamedTemporaryFile('w', delete=False, dir=config_dir) as temp_file:
                json.dump(data, temp_file, indent=4)
                temp_file_path = temp_file.name

            # Atomic replace
            if os.path.exists(filepath):
                os.remove(filepath)
            os.rename(temp_file_path, filepath)
            return True

        except Exception as e:
            print(f"Error saving {filename}: {e}")
            # Cleanup temporary file if it exists
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return False