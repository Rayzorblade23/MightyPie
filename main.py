import sys
import threading

import keyboard
from PyQt6.QtWidgets import (
    QApplication,
    QWidget, )

from color_functions import adjust_saturation
from config import CONFIG
from events import ShowWindowEvent, HotkeyReleaseEvent
from global_mouse_filter import GlobalMouseFilter
from pie_window import PieWindow
from window_manager import WindowManager


def listen_for_hotkeys(main_window: QWidget):
    """Listen for global hotkeys."""

    can_open_window = True  # Track window state

    def on_press():
        nonlocal can_open_window
        if can_open_window:  # Only show if not already open
            print("Hotkey pressed! Opening switcherino...")
            show_event = ShowWindowEvent(main_window)
            QApplication.postEvent(main_window, show_event)
            can_open_window = False

    def on_release():
        nonlocal can_open_window
        print("Hotkey released!")
        release_event = HotkeyReleaseEvent(main_window)
        QApplication.postEvent(main_window, release_event)
        can_open_window = True  # Reset the state

    keyboard.on_press_key(CONFIG.HOTKEY_OPEN, lambda _: on_press(),suppress=True)
    keyboard.on_release_key(CONFIG.HOTKEY_OPEN, lambda _: on_release())
    keyboard.wait()


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

    # Create and show the main main_window
    window = PieWindow()

    # Install the GlobalMouseFilter
    global_mouse_filter = GlobalMouseFilter(window)
    app.installEventFilter(global_mouse_filter)

    # Show the main_window briefly and immediately hide it
    window.show()  # Make sure the main_window is part of the filtered_event loop

    event = ShowWindowEvent(window)
    # Post the filtered_event to the main thread
    QApplication.postEvent(window, event)

    # main_window.hide()  # Hide it right after showing

    # Hotkey Thread
    hotkey_thread = threading.Thread(
        target=listen_for_hotkeys, args=(window,), daemon=True
    )
    hotkey_thread.start()

    # main_window.auto_refresh()

    sys.exit(app.exec())
