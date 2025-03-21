# data/temp_button_config.py
import logging
from typing import Any, Dict, Optional

from src.data.button_info import ButtonInfo

logger = logging.getLogger(__name__)


class TemporaryButtonConfig:
    """Temporarily stores button configuration changes until saved."""

    def __init__(self):
        self._temp_changes = {}

    def get_button_config(self, button_index: int) -> Optional[Dict[str, Any]]:
        """Gets the temporary configuration for a button."""
        return self._temp_changes.get(button_index)

    def update_button(self, index: int, changes: dict) -> None:
        logger.debug(f"TemporaryButtonConfig.update_button called with index: {index}, changes: {changes}")
        if index not in self._temp_changes:
            self._temp_changes[index] = {"task_type": "", "properties": {}}

        # Update task_type if provided
        if "task_type" in changes:
            self._temp_changes[index]["task_type"] = changes["task_type"]

        # Update or merge properties if provided
        if "properties" in changes:
            self._temp_changes[index]["properties"].update(changes["properties"])

        logger.debug(f"Updated temp changes for index {index}: {self._temp_changes[index]}")

    def apply_changes(self, button_info: ButtonInfo) -> None:
        for index, changes in self._temp_changes.items():
            button_info.update_button(index, changes)
        logger.info("Applied temporary button configuration changes.")
        self.clear()

    def clear(self) -> None:
        self._temp_changes.clear()

    def has_changes(self) -> bool:
        return bool(self._temp_changes)