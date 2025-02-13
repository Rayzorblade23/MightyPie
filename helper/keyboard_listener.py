from typing import TYPE_CHECKING

import keyboard
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication, QWidget

from data.config import CONFIG
from events import ShowWindowEvent, HotkeyReleaseEvent

if TYPE_CHECKING:
    from gui.pie_window import PieWindow

class HotkeyListener:
    """Listens for global hotkeys and triggers corresponding actions."""

    def __init__(self, main_window: 'PieWindow'):
        """
        Initializes the HotkeyListener with a reference to the main window.

        Args:
            main_window (QWidget): The main application window.
        """
        self.main_window = main_window
        self.can_open_window = True  # Track window state
        self.initial_mouse_pos = None  # Store initial mouse position on press

    def start_listening(self):
        """Starts listening for the configured hotkeys."""
        keyboard.on_press_key(CONFIG.HOTKEY_PRIMARY, lambda _: self.on_press(CONFIG.HOTKEY_PRIMARY), suppress=True)
        keyboard.on_release_key(CONFIG.HOTKEY_PRIMARY, lambda _: self.on_release(CONFIG.HOTKEY_PRIMARY))

        keyboard.on_press_key(CONFIG.HOTKEY_SECONDARY, lambda _: self.on_press(CONFIG.HOTKEY_SECONDARY), suppress=True)
        keyboard.on_release_key(CONFIG.HOTKEY_SECONDARY, lambda _: self.on_release(CONFIG.HOTKEY_SECONDARY))

        keyboard.wait()

    def on_press(self, hotkey_name: str):
        """Handles hotkey press events."""
        if not self.can_open_window:
            return  # Only show if not already open

        print(f"{hotkey_name} pressed!")
        self.initial_mouse_pos = QCursor.pos()  # Store initial mouse position using QCursor

        if hotkey_name == CONFIG.HOTKEY_PRIMARY:
            child_window, main_window_active_child = self._get_next_task_switcher()
            self.main_window.active_child = main_window_active_child

        elif hotkey_name == CONFIG.HOTKEY_SECONDARY:
            child_window, main_window_active_child = self._get_next_win_control()
            self.main_window.active_child = main_window_active_child

        else:
            print("Hotkey not found.")
            return

        if child_window:
            show_event = ShowWindowEvent(self.main_window, child_window)
            QApplication.postEvent(self.main_window, show_event)
            self.can_open_window = False

    def on_release(self, hotkey_name: str):
        """Handles hotkey release events."""
        # Get current mouse position
        current_mouse_pos = QCursor.pos()
        # Check if the mouse has moved beyond a threshold (e.g., 10 pixels)
        if (self.initial_mouse_pos is not None and
                (abs(current_mouse_pos.x() - self.initial_mouse_pos.x()) <= 35) and
                (abs(current_mouse_pos.y() - self.initial_mouse_pos.y()) <= 35)):
            # print("Mouse released without movement.")
            self.can_open_window = True

        else:
            if hotkey_name == CONFIG.HOTKEY_PRIMARY:
                # Select the task switcher based on the active_child value
                index = self.main_window.active_child - 1
                # Check if in range for Task Switchers
                if 0 <= index <= len(self.main_window.pm_task_switchers) - 1:
                    child_window = self.main_window.pm_task_switchers[index]
                else:
                    print("Active child index is out of range for task switchers.")
                    return
            elif hotkey_name == CONFIG.HOTKEY_SECONDARY:
                # Select the task switcher based on the active_child value
                index = self.main_window.active_child - 1 - len(self.main_window.pm_task_switchers)
                # Check if in range for WinControls
                if 0 <= index <= len(self.main_window.pm_task_switchers) - 1:
                    child_window = self.main_window.pm_win_controls[index]
                else:
                    print("Active child index is out of range for task switchers.")
                    return
            else:
                print("Hotkey not found.")
                return

            if child_window:
                release_event = HotkeyReleaseEvent(self.main_window, child_window)
                QApplication.postEvent(self.main_window, release_event)
                self.can_open_window = True  # Reset the state

    def _get_next_task_switcher(self):
        """Helper to find the next task switcher to toggle."""
        pm_task_switchers = getattr(self.main_window, 'pm_task_switchers', None)
        if not pm_task_switchers or not isinstance(pm_task_switchers, list):
            print("Warning: Task switchers are not instantiated.")
            return None, None

        # Find the first task switcher to toggle or open the next one
        for index, task_switcher in enumerate(pm_task_switchers):
            if task_switcher.isVisible():
                # Toggle to the next task switcher or back to the first
                next_index = (index + 1) % len(pm_task_switchers)
                child_window = pm_task_switchers[next_index]
                main_window_active_child = next_index + 1
                return child_window, main_window_active_child
        else:
            # If none are visible, open the first task switcher
            child_window = pm_task_switchers[0]
            main_window_active_child = 1
            return child_window, main_window_active_child

    def _get_next_win_control(self):
        """Helper to find the next window control to toggle."""
        pm_win_controls = getattr(self.main_window, 'pm_win_controls', None)
        pm_task_switchers = getattr(self.main_window, 'pm_task_switchers', None)
        if not pm_win_controls or not isinstance(pm_win_controls, list):
            print("Warning: Task switchers are not instantiated.")
            return None, None

        # Find the first task switcher to toggle or open the next one
        for index, win_control in enumerate(pm_win_controls):
            if win_control.isVisible():
                # Toggle to the next task switcher or back to the first
                next_index = (index + 1) % len(pm_win_controls)
                child_window = pm_win_controls[next_index]
                main_window_active_child = len(pm_task_switchers) + next_index + 1
                return child_window, main_window_active_child
        else:
            # If none are visible, open the first task switcher
            child_window = pm_win_controls[0]
            main_window_active_child = len(pm_task_switchers) + 1
            return child_window, main_window_active_child