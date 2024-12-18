import sys
import threading

import keyboard
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
)

from config import CONFIG
from events import ShowWindowEvent
from task_switcher_pie import TaskSwitcherPie
from window_manager import WindowManager


def listen_for_hotkeys(window: QWidget):
    """Listen for global hotkeys."""

    def wrapper():
        print(
            "Hotkey pressed! Opening switcherino..."
        )  # Debugging: Check if hotkey is detected
        # Post the custom event to the window's event queue
        event = ShowWindowEvent(window)
        # Post the event to the main thread
        QApplication.postEvent(window, event)

    keyboard.add_hotkey(CONFIG.HOTKEY_OPEN, wrapper, suppress=True)
    keyboard.wait()


import colorsys


def adjust_saturation(hex_color, saturation_factor=0.8):
    """Adjust the saturation of a hex color."""
    # Convert hex to RGB
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)

    # Normalize RGB to [0, 1]
    r, g, b = r / 255.0, g / 255.0, b / 255.0

    # Convert RGB to HSL
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    # Adjust saturation
    s = max(0, min(1, s * saturation_factor))  # Ensure saturation stays within [0, 1]

    # Convert HSL back to RGB
    r, g, b = colorsys.hls_to_rgb(h, l, s)

    # Convert RGB back to hex
    return f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # creating hues
    accent_color_muted = adjust_saturation(CONFIG.ACCENT_COLOR, 0.5)

    # Load the QSS template
    with open("style.qss", "r") as file:
        qss_template = file.read()

    # inserting style attributes from the config.py file
    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", accent_color_muted)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    # Apply the QSS to the application or widgets
    app.setStyleSheet(qss)

    manager = WindowManager.get_instance()

    # Create and show the main window
    window = TaskSwitcherPie()

    # Show the window briefly and immediately hide it
    window.show()  # Make sure the window is part of the event loop
    # window.hide()  # Hide it right after showing

    # Hotkey Thread
    hotkey_thread = threading.Thread(
        target=listen_for_hotkeys, args=(window,), daemon=True
    )
    hotkey_thread.start()

    # Initial Refresh and Auto-refresh
    # window.refresh()
    window.auto_refresh()

    sys.exit(app.exec())
