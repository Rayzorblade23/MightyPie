from typing import TYPE_CHECKING

import keyboard
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication, QWidget

from data.config import CONFIG
from events import ShowWindowEvent, HotkeyReleaseEvent
from gui.menus.pie_menu import PrimaryPieMenu, SecondaryPieMenu

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

        # print(f"{hotkey_name} pressed!")
        self.initial_mouse_pos = QCursor.pos()  # Store initial mouse position using QCursor

        if hotkey_name == CONFIG.HOTKEY_PRIMARY:
            pie_menu, main_window_active_child = self.main_window.get_next_pie_menu_on_hotkey_press(PrimaryPieMenu)
            self.main_window.active_child = main_window_active_child

        elif hotkey_name == CONFIG.HOTKEY_SECONDARY:
            pie_menu, main_window_active_child = self.main_window.get_next_pie_menu_on_hotkey_press(SecondaryPieMenu)
            self.main_window.active_child = main_window_active_child

        else:
            print("Hotkey not found.")
            return

        if pie_menu:
            show_event = ShowWindowEvent(self.main_window, pie_menu)
            QApplication.postEvent(self.main_window, show_event)
            self.can_open_window = False

    def on_release(self, hotkey_name: str):
        """Handles hotkey release events."""
        # Ensure cursor_displacement is valid (i.e., has been set)
        if self.main_window.cursor_displacement is None:
            print("Error: cursor_displacement is not set. Skipping drag check.")
            self.can_open_window = True  # Allow reopening window
            return

        # Ensure initial_mouse_pos is not None
        if self.initial_mouse_pos is None:
            print("Error: initial_mouse_pos is not set. Skipping drag calculation.")
            return

        # Get current mouse position
        current_mouse_pos = QCursor.pos()

        # Calculate the movement, factoring in the cursor displacement
        displacement_x = current_mouse_pos.x() - self.initial_mouse_pos.x() - self.main_window.cursor_displacement[0]
        displacement_y = current_mouse_pos.y() - self.initial_mouse_pos.y() - self.main_window.cursor_displacement[1]

        # If the displacement is below the threshold, it's considered a click, not a drag
        if abs(displacement_x) <= 35 and abs(displacement_y) <= 35:
            self.can_open_window = True  # Allow reopening the window


        # Else we invoke the drag-to-select functionality
        else:
            if hotkey_name == CONFIG.HOTKEY_PRIMARY:
                pie_menu = self.main_window.get_pie_menu_after_hotkey_drag(PrimaryPieMenu)
            elif hotkey_name == CONFIG.HOTKEY_SECONDARY:
                pie_menu = self.main_window.get_pie_menu_after_hotkey_drag(SecondaryPieMenu)
            else:
                print("Hotkey not found.")
                return

            if pie_menu:
                release_event = HotkeyReleaseEvent(self.main_window, pie_menu)
                QApplication.postEvent(self.main_window, release_event)
                self.can_open_window = True  # Reset the state
