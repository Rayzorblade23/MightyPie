from dataclasses import dataclass, field

from functions.color_functions import adjust_saturation


@dataclass
class TaskPieSwitcherConfig:
    PROGRAM_NAME: str = "MightyPie"
    CACHE_FILENAME: str = "apps_info_cache.json"
    REFRESH_INTERVAL: int = 3000  # ms
    TASKBAR_OPACITY: int = 150
    HOTKEY_OPEN_TASKS: str = "F14"
    HOTKEY_OPEN_WINCON: str = "F13"
    MAX_BUTTONS: int = 8
    NUM_PIE_MENUS: int = 2
    BUTTON_WIDTH: int = 140
    BUTTON_HEIGHT: int = 34
    CONTROL_BUTTON_SIZE: int = 30
    # WINDOW_WIDTH: int = 1200
    # WINDOW_HEIGHT: int = 800
    CANVAS_SIZE: int = 800, 600
    RADIUS: int = 150
    INNER_RADIUS: int = 18
    PIE_TEXT_LABEL_MARGINS: int = 10
    PIE_TEXT_LABEL_SCROLL_SPEED: int = 1
    PIE_TEXT_LABEL_SCROLL_INTERVAL: int = 25
    ACCENT_COLOR: str = "#5a14b7"
    ACCENT_COLOR_MUTED: str = adjust_saturation(ACCENT_COLOR, 0.5)
    BG_COLOR: str = "#3b3b3b"
    FIXED_PIE_SLOTS: dict[str, tuple[int, str]] = field(default_factory=lambda: {
        "Spotify": (4, "spotify.exe"),
        "Vivaldi": (0, "vivaldi.exe"),
        "Telegram Desktop": (6, "telegram.exe")
    })


CONFIG = TaskPieSwitcherConfig()
