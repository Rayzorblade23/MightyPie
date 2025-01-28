import os
import signal
import sys
import threading
import warnings

warnings.simplefilter("ignore", UserWarning)
sys.coinit_flags = 2
import keyboard
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QApplication,
    QWidget, )

from config import CONFIG
from events import ShowWindowEvent, HotkeyReleaseEvent
from functions.file_handling_functions import get_resource_path
from functions.taskbar_hide_utils import set_taskbar_opacity, show_taskbar
from global_mouse_filter import GlobalMouseFilter
from pie_window import PieWindow


def listen_for_hotkeys(main_window: QWidget):
    """Listen for global hotkeys."""
    can_open_window = True  # Track window state
    initial_mouse_pos = None  # Store initial mouse position on press

    # Assign variables at the start
    pm_win_control = getattr(main_window, 'pm_win_control', None)
    pm_task_switchers = getattr(main_window, 'pm_task_switchers', None)

    # Check if any of the necessary windows are None (not instantiated)
    if not pm_win_control or not pm_task_switchers or not isinstance(pm_task_switchers, list) or not pm_task_switchers:
        print("Warning: Task switchers or window control are not instantiated.")
        return

    def on_press(hotkey_name: str):
        nonlocal can_open_window, initial_mouse_pos
        if can_open_window:  # Only show if not already open
            print(f"{hotkey_name} pressed!")
            initial_mouse_pos = QCursor.pos()  # Store initial mouse position using QCursor

            child_window = None  # Default to no child window

            if hotkey_name == CONFIG.HOTKEY_OPEN_TASKS:
                # Find the first task switcher to toggle or open the next one
                for index, task_switcher in enumerate(pm_task_switchers):
                    if task_switcher.isVisible():
                        # Toggle to the next task switcher or back to the first
                        next_index = (index + 1) % len(pm_task_switchers)
                        child_window = pm_task_switchers[next_index]
                        main_window.active_child = next_index + 1
                        break
                else:
                    # If none are visible, open the first task switcher
                    child_window = pm_task_switchers[0]
                    main_window.active_child = 1

            elif hotkey_name == CONFIG.HOTKEY_OPEN_WINCON:
                child_window = pm_win_control
                main_window.active_child = 4
            else:
                print("Hotkey not found.")
                return

            if child_window:
                show_event = ShowWindowEvent(main_window, child_window)
                QApplication.postEvent(main_window, show_event)
                can_open_window = False

    def on_release(hotkey_name: str):
        nonlocal can_open_window, initial_mouse_pos

        # Get current mouse position
        current_mouse_pos = QCursor.pos()
        child_window = None
        # Check if the mouse has moved beyond a threshold (e.g., 10 pixels)
        if (initial_mouse_pos is not None and
                (abs(current_mouse_pos.x() - initial_mouse_pos.x()) <= 10) and
                (abs(current_mouse_pos.y() - initial_mouse_pos.y()) <= 10)):
            # print("Mouse released without movement.")
            can_open_window = True

        else:

            # print("Mouse released WITH movement.")
            if hotkey_name == CONFIG.HOTKEY_OPEN_TASKS:
                if 1 <= main_window.active_child <= len(pm_task_switchers):
                    # Select the task switcher based on the active_child value
                    child_window = pm_task_switchers[main_window.active_child - 1]
                else:
                    print("Active child index is out of range for task switchers.")
                    return
            elif hotkey_name == CONFIG.HOTKEY_OPEN_WINCON:
                child_window = pm_win_control
            else:
                print("Hotkey not found.")
                return

            if child_window:
                release_event = HotkeyReleaseEvent(main_window, child_window)
                QApplication.postEvent(main_window, release_event)
                can_open_window = True  # Reset the state

    # def handle_mouse_click(x, y, button, pressed):
    #     """Handle mouse button events."""
    #     if button == MouseButton.x2:  # Forward button
    #         if pressed:
    #             print("PRESSED")
    #             on_press()
    #         else:
    #             print("RELEASED")
    #             on_release()

    # Start mouse listener in a separate thread
    # mouse_listener = MouseListener(on_click=handle_mouse_click)
    # mouse_listener.start()

    keyboard.on_press_key(CONFIG.HOTKEY_OPEN_TASKS, lambda _: on_press(CONFIG.HOTKEY_OPEN_TASKS), suppress=True)
    keyboard.on_release_key(CONFIG.HOTKEY_OPEN_TASKS, lambda _: on_release(CONFIG.HOTKEY_OPEN_TASKS))

    keyboard.on_press_key(CONFIG.HOTKEY_OPEN_WINCON, lambda _: on_press(CONFIG.HOTKEY_OPEN_WINCON), suppress=True)
    keyboard.on_release_key(CONFIG.HOTKEY_OPEN_WINCON, lambda _: on_release(CONFIG.HOTKEY_OPEN_WINCON))

    keyboard.wait()


def signal_handler(signal, frame):
    # Ensure taskbar is shown before exiting
    show_taskbar()
    # toggle_taskbar_autohide(False)
    sys.exit(0)


if __name__ == "__main__":
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'

    # Register signal handler for SIGINT (Ctrl+C) and SIGTERM (termination signals)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("MightyPie")

    set_taskbar_opacity(CONFIG.TASKBAR_OPACITY)

    # Load the QSS template
    with open(get_resource_path("style.qss"), "r") as file:
        qss_template = file.read()

    # inserting style attributes from the config.py file
    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", CONFIG.ACCENT_COLOR_MUTED)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    # Apply the QSS to the application or widgets
    app.setStyleSheet(qss)

    # Create and show the main main_window
    window = PieWindow()

    # Install the GlobalMouseFilter
    global_mouse_filter = GlobalMouseFilter(window)
    app.installEventFilter(global_mouse_filter)

    # Show the main_window briefly and immediately hide it
    window.show()  # Make sure the main_window is part of the filtered_event loop
    window.hide()

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
