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
            child_window, main_window_active_child = self._get_next_pie_menu("task_switcher")
            self.main_window.active_child = main_window_active_child

        elif hotkey_name == CONFIG.HOTKEY_SECONDARY:
            child_window, main_window_active_child = self._get_next_pie_menu("win_control")
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
                if 0 <= index <= len(self.main_window.pie_menus_primary) - 1:
                    child_window = self.main_window.pie_menus_primary[index]
                else:
                    print("Active child index is out of range for task switchers.")
                    return
            elif hotkey_name == CONFIG.HOTKEY_SECONDARY:
                # Select the task switcher based on the active_child value
                index = self.main_window.active_child - 1 - len(self.main_window.pie_menus_primary)
                # Check if in range for WinControls
                if 0 <= index <= len(self.main_window.pie_menus_primary) - 1:
                    child_window = self.main_window.pie_menus_secondary[index]
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

    def _get_next_pie_menu(self, menu_type):
        """Helper to find the next pie menu (task switcher or window control) to toggle.

        Args:
            menu_type:  A string, either 'task_switcher' or 'win_control', indicating which
                        type of pie menu to search for.

        Returns:
            A tuple containing the next child window to activate and its corresponding
            main_window_active_child index.  Returns (None, None) if an error occurs
            or the specified menu type is invalid.
        """

        if menu_type == 'task_switcher':
            pie_menus = getattr(self.main_window, 'pie_menus_primary', None)
            offset = 0  # Task switchers start at index 1 in main_window_active_child
        elif menu_type == 'win_control':
            pie_menus = getattr(self.main_window, 'pie_menus_secondary', None)
            pm_task_switchers = getattr(self.main_window, 'pie_menus_primary',
                                        None)  # Required for proper main_window_active_child index calculation
            if pm_task_switchers:
                offset = len(pm_task_switchers)  # Window controls start after task switchers
            else:
                offset = 0
        else:
            print(f"Warning: Invalid menu_type: {menu_type}")
            return None, None

        if not pie_menus or not isinstance(pie_menus, list):
            print(f"Warning: {menu_type.replace('_', ' ').title()}s are not instantiated.")
            return None, None

        # Find the first pie menu to toggle or open the next one
        for index, pie_menu in enumerate(pie_menus):
            if pie_menu.isVisible():
                # Toggle to the next pie menu or back to the first
                next_index = (index + 1) % len(pie_menus)
                child_window = pie_menus[next_index]
                main_window_active_child = offset + next_index + 1
                return child_window, main_window_active_child
        else:
            # If none are visible, open the first pie menu
            child_window = pie_menus[0]
            main_window_active_child = offset + 1
            return child_window, main_window_active_child