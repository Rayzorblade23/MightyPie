from typing import Callable, Union, Dict

import pyautogui
from PyQt6.QtWidgets import QApplication

from data.icon_paths import EXTERNAL_ICON_PATHS
from utils.functions_utils import close_window_at_cursor, restore_last_minimized_window, minimize_window_at_cursor, \
    toggle_maximize_window_at_cursor, center_window_at_cursor, focus_all_explorer_windows, restart_explorer


class ButtonFunctions:
    """Encapsulates button functions and their metadata."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self.__initialized:
            return
        self.__initialized = True

        self.functions: Dict[str, Dict[str, Union[str, Callable, str]]] = {
            "toggle_maximize_window": {
                "text_1": "Maximize",
                "action": self._wrap(toggle_maximize_window_at_cursor),
                "icon": EXTERNAL_ICON_PATHS.get("window_maximize"),
            },
            "restore_minimized_window": {
                "text_1": "Restore Mini.",
                "action": restore_last_minimized_window,
                "icon": EXTERNAL_ICON_PATHS.get("change"),
            },
            "navigation_forward": {
                "text_1": "Forward",
                "action": lambda: pyautogui.hotkey("alt", "right"),
                "icon": EXTERNAL_ICON_PATHS.get("arrow-right"),
            },
            "navigation_backwards": {
                "text_1": "Backwards",
                "action": lambda: pyautogui.hotkey("alt", "left"),
                "icon": EXTERNAL_ICON_PATHS.get("arrow-left"),
            },
            "copy": {
                "text_1": "Copy",
                "action": lambda: pyautogui.hotkey("ctrl", "c"),
                "icon": EXTERNAL_ICON_PATHS.get("copy"),
            },
            "paste": {
                "text_1": "Paste",
                "action": lambda: pyautogui.hotkey("ctrl", "v"),
                "icon": EXTERNAL_ICON_PATHS.get("clipboard"),
            },
            "clipboard": {
                "text_1": "Clipboard",
                "action": lambda: pyautogui.hotkey("win", "v"),
                "icon": EXTERNAL_ICON_PATHS.get("clipboard-search"),
            },
            "fullscreen_11": {
                "text_1": "Fullscreen (F11)",
                "action": lambda: pyautogui.press('f11'),
                "icon": EXTERNAL_ICON_PATHS.get("fullscreen"),
            },
            "media_play_pause": {
                "text_1": "Play/Pause",
                "action": lambda: pyautogui.press('playpause'),
                "icon": EXTERNAL_ICON_PATHS.get("media-play"),
            },
            "media_skip_forward": {
                "text_1": "Next Track",
                "action": lambda: pyautogui.press('nexttrack'),
                "icon": EXTERNAL_ICON_PATHS.get("media-skip-forward"),
            },
            "media_skip_backward": {
                "text_1": "Previous Track",
                "action": lambda: pyautogui.press('prevtrack'),
                "icon": EXTERNAL_ICON_PATHS.get("media-skip-backward"),
            },
            "media_mute": {
                "text_1": "Mute",
                "action": lambda: pyautogui.press('volumemute'),
                "icon": EXTERNAL_ICON_PATHS.get("media-mute"),
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
            "close_window": {
                "text_1": "Close Window",
                "action": self._wrap(close_window_at_cursor),
                "icon": EXTERNAL_ICON_PATHS.get("quit"),
            },
            "restart_explorer": {
                "text_1": "Restart Explorer",
                "action": restart_explorer,
                "icon": EXTERNAL_ICON_PATHS.get("restart"),
            },
            # "open_pie_menu": {
            #     "text_1": "Open Pie",
            #     "action": open_pie_menu,
            #     "icon": EXTERNAL_ICON_PATHS.get("center"),
            # },
        }

    @staticmethod
    def _wrap(func: Callable) -> Callable[[], None]:
        """Wraps functions to pass the main_window as an argument."""

        def wrapped():
            main_window = QApplication.instance().property("main_window")
            if main_window:
                return func(main_window)

        return wrapped

    def get_function(self, key: str) -> dict:
        """Returns the function metadata for a given key, or raises an error if the key doesn't exist."""
        func = self.functions.get(key)
        if func is None:
            raise KeyError(f"Function key '{key}' not found.")
        return func
