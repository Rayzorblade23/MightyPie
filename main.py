import sys
import threading

import keyboard
from PyQt6.QtGui import QCursor, QGuiApplication
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
    initial_mouse_pos = None  # Store initial mouse position on press

    def on_press():
        nonlocal can_open_window, initial_mouse_pos
        if can_open_window:  # Only show if not already open
            print("Hotkey pressed! Opening switcherino...")
            initial_mouse_pos = QCursor.pos()  # Store initial mouse position using QCursor
            if main_window.isVisible():
                child_window = getattr(main_window, 'pm_task_switcher_2', None)
                main_window.active_child = 2
            else:
                child_window = getattr(main_window, 'pm_task_switcher', None)
                main_window.active_child = 1
            show_event = ShowWindowEvent(main_window, child_window)
            QApplication.postEvent(main_window, show_event)
            can_open_window = False

    def on_release():
        nonlocal can_open_window, initial_mouse_pos
        print("Hotkey released!")

        # Get current mouse position
        current_mouse_pos = QCursor.pos()

        # Check if the mouse has moved beyond a threshold (e.g., 10 pixels)
        if initial_mouse_pos and (abs(current_mouse_pos.x() - initial_mouse_pos.x()) <= 10) and \
                (abs(current_mouse_pos.y() - initial_mouse_pos.y()) <= 10):
            print("Mouse hasn't moved. Keeping window open")
            can_open_window = True
        else:
            if main_window.active_child == 2:
                child_window = getattr(main_window, 'pm_task_switcher_2', None)
            elif main_window.active_child == 1:
                child_window = getattr(main_window, 'pm_task_switcher', None)
            release_event = HotkeyReleaseEvent(main_window, child_window)
            QApplication.postEvent(main_window, release_event)
            can_open_window = True  # Reset the state

    keyboard.on_press_key(CONFIG.HOTKEY_OPEN, lambda _: on_press(), suppress=True)
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
