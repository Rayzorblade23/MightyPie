# data/temp_button_config.py
import logging
from data.button_info import ButtonInfo

class TemporaryButtonConfig:
    """Temporarily stores button configuration changes until saved."""

    def __init__(self):
        self._temp_changes = {}

    def update_button(self, index: int, changes: dict) -> None:
        logging.debug(f"TemporaryButtonConfig.update_button called with index: {index}, changes: {changes}")
        if index not in self._temp_changes:
            self._temp_changes[index] = {"task_type": "", "properties": {}}

        # Update task_type if provided
        if "task_type" in changes:
            self._temp_changes[index]["task_type"] = changes["task_type"]

        # Update or merge properties if provided
        if "properties" in changes:
            self._temp_changes[index]["properties"].update(changes["properties"])

        logging.debug(f"Updated temp changes for index {index}: {self._temp_changes[index]}")

    def apply_changes(self, button_info: ButtonInfo) -> None:
        for index, changes in self._temp_changes.items():
            button_info.update_button(index, changes)
        self.clear()

    def clear(self) -> None:
        self._temp_changes.clear()

    def has_changes(self) -> bool:
        return bool(self._temp_changes)