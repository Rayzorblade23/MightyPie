from dataclasses import dataclass
import os


@dataclass
class TaskPieSwitcherConfig:
    CACHE_FILE: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "app_name_cache.json"
    )
    REFRESH_INTERVAL: int = 2000  # ms
    HOTKEY_OPEN: str = "F1"
    MAX_BUTTONS: int = 8
    BUTTON_WIDTH: int = 150
    BUTTON_HEIGHT: int = 38
    CONTROL_BUTTON_SIZE: int = 30
    WINDOW_WIDTH: int = 600
    WINDOW_HEIGHT: int = 400
    CANVAS_SIZE: int = 600, 400
    RADIUS: int = 150
    INNER_RADIUS: int = 18
    PIE_TEXT_LABEL_MARGINS: int = 10
    PIE_TEXT_LABEL_SCROLL_SPEED: int = 1
    PIE_TEXT_LABEL_SCROLL_INTERVAL: int = 16



CONFIG = TaskPieSwitcherConfig()
