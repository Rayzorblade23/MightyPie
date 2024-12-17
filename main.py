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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the stylesheet
    with open("style.qss", "r") as file:
        app.setStyleSheet(file.read())

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
