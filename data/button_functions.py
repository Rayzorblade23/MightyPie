from typing import TYPE_CHECKING, Callable, Union, Dict

import pyautogui
from PyQt6.QtWidgets import QApplication

from data.icon_paths import EXTERNAL_ICON_PATHS
from utils.window_utils import (
    toggle_maximize_window_at_cursor,
    minimize_window_at_cursor,
    center_window_at_cursor,
    restore_last_minimized_window,
    focus_all_explorer_windows,
)

if TYPE_CHECKING:
    from gui.pie_window import PieWindow


class ButtonFunctions:
    """Encapsulates button functions and their metadata."""

    def __init__(self) -> None:
        self.main_window: "PieWindow" = QApplication.instance().property("main_window")
        self.functions: Dict[str, Dict[str, Union[str, Callable, str]]] = {
            "toggle_maximize_window": {
                "text_1": "MAXIMIZE",
                "action": self._wrap(toggle_maximize_window_at_cursor),
                "icon": EXTERNAL_ICON_PATHS.get("window_maximize"),
            },
            "restore_minimized_window": {
                "text_1": "Restore Minimized",
                "action": restore_last_minimized_window,
                "icon": EXTERNAL_ICON_PATHS.get("change"),
            },
            "navigation_forward": {
                "text_1": "Forward",
                "action": lambda: pyautogui.hotkey("alt", "right"),
                "icon": EXTERNAL_ICON_PATHS.get("arrow-right"),
            },
            "focus_all_explorer_windows": {
                "text_1": "Get All Expl. Win.",
                "action": focus_all_explorer_windows,
                "icon": EXTERNAL_ICON_PATHS.get("folders"),
            },
            "minimize_window": {
                "text_1": "Minimize",
                "action": self._wrap(minimize_window_at_cursor),
                "icon": EXTERNAL_ICON_PATHS.get("window_minimize"),
            },
            "center_window": {
                "text_1": "Center Window",
                "action": self._wrap(center_window_at_cursor),
                "icon": EXTERNAL_ICON_PATHS.get("center"),
            },
        }

    def _wrap(self, func: Callable) -> Callable[[], None]:
        """Wraps functions to pass the main_window as an argument."""
        return lambda: func(self.main_window)

    def get_function(self, key: str) -> dict:
        """Returns the function metadata for a given key, or raises an error if the key doesn't exist."""
        func = self.functions.get(key)
        if func is None:
            raise KeyError(f"Function key '{key}' not found.")
        return func
