# data/button_config_manager.py
import logging
from typing import Dict, Any, Optional

from src.data.button_info import ButtonInfo
from src.data.temp_button_config import TemporaryButtonConfig

logger = logging.getLogger(__name__)


class ButtonConfigManager:
    """Manages button configuration state and changes."""

    def __init__(self):
        self.button_info = ButtonInfo.get_instance()
        self.temp_config = TemporaryButtonConfig()

        logger.info("ButtonConfigManager initialized.")

    def update_task_type(self, button_index: int, task_type: str) -> None:
        """Updates the task type for a button and sets default properties."""
        try:
            default_properties = ButtonInfo.get_default_properties(task_type)
            self.temp_config.update_button(button_index, {
                "task_type": task_type,
                "properties": default_properties
            })
        except Exception as e:
            logging.error(f"Failed to update task type: {str(e)}")
            raise

    def update_value(self, button_index: int, value: str, task_type: Optional[str] = None) -> None:
        """Updates the value (exe name or function name) for a button."""
        try:
            current_config = self.get_current_config(button_index)
            task_type = task_type or current_config["task_type"]
            current_properties = current_config.get("properties", {}).copy()

            if task_type == "call_function":
                current_properties["function_name"] = value
            else:
                current_properties["exe_name"] = value

            self.temp_config.update_button(button_index, {
                "task_type": task_type,
                "properties": current_properties
            })
            logging.debug(f"Updated value for button {button_index}: {value}")
        except Exception as e:
            logging.error(f"Failed to update value: {str(e)}")
            raise

    def get_current_config(self, button_index: int) -> Dict[str, Any]:
        """Gets the current configuration for a button."""
        return self.temp_config.get_button_config(button_index) or self.button_info[button_index]

    def reset_button(self, button_index: int) -> None:
        """Resets a single button to default configuration."""
        try:
            self.temp_config.update_button(button_index, {
                "task_type": "show_any_window",
                "properties": ButtonInfo.get_default_properties("show_any_window")
            })
            logging.debug(f"Reset button {button_index} to defaults")
        except Exception as e:
            logging.error(f"Failed to reset button: {str(e)}")
            raise

    def reset_all(self) -> None:
        """Resets all buttons to default configuration."""
        try:
            for button_index in range(40):  # Assuming 40 buttons total
                self.reset_button(button_index)
            logging.debug("Reset all buttons to defaults")
        except Exception as e:
            logging.error(f"Failed to reset all buttons: {str(e)}")
            raise

    def save_changes(self) -> None:
        """Saves all changes to permanent storage."""
        try:
            self.temp_config.apply_changes(self.button_info)
            sorted_config = dict(sorted(
                self.button_info.button_info_dict.items(),
                key=lambda x: int(x[0])
            ))
            self.button_info.button_info_dict = sorted_config
            self.button_info.save_to_json()
            self.temp_config.clear()
            logging.debug("Saved all changes to permanent storage")
        except Exception as e:
            logging.error(f"Failed to save changes: {str(e)}")
            raise

    def has_unsaved_changes(self) -> bool:
        """Checks if there are any unsaved changes."""
        return self.temp_config.has_changes()

    def discard_changes(self) -> None:
        """Discards all temporary changes."""
        self.temp_config.clear()
        self.button_info.load_json()
        logging.debug("Discarded all temporary changes")
