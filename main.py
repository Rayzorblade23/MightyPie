import sys
import threading
from sys import dont_write_bytecode

import keyboard
from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
)

from color_functions import adjust_saturation
from config import CONFIG
from events import ShowWindowEvent
from task_switcher_pie import TaskSwitcherPie
from window_manager import WindowManager

class GlobalMouseFilter(QObject):
    def __init__(self, donut_button):
        super().__init__()
        self.donut_button = donut_button  # Reference to the button for state updates

    def eventFilter(self, obj, event):
        if isinstance(event, QMouseEvent):
            global_pos = event.globalPosition().toPoint()

            if event.type() == QEvent.Type.MouseMove:
                local_pos = self.donut_button.mapFromGlobal(global_pos)
                self.donut_button.turn_towards_cursor(local_pos)


        return super().eventFilter(obj, event)


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

    # Install the global mouse event filter
    global_mouse_filter = GlobalMouseFilter(window.donut_button)
    app.installEventFilter(global_mouse_filter)

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
