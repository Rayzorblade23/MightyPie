import threading
import time
from typing import TYPE_CHECKING

import keyboard
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication, QWidget
from keyboard import on_press, on_release

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
        self.hotkey_states = {}  # Track active hotkeys

        self.thread_events = {}  # Track thread events for monitoring thread completion
        self.active_threads = []  # Track active threads

    def start_listening(self):
        """Starts listening for the configured hotkeys."""

        # Listen for press and trigger on_press
        keyboard.add_hotkey(CONFIG.HOTKEY_PRIMARY, lambda: self.handle_press(CONFIG.HOTKEY_PRIMARY), suppress=True)
        keyboard.add_hotkey(CONFIG.HOTKEY_SECONDARY, lambda: self.handle_press(CONFIG.HOTKEY_SECONDARY), suppress=True)

        keyboard.wait()  # Keep the listener running

    def handle_press(self, hotkey_name: str):
        """Handles hotkey press and starts a release monitor if needed."""
        if self.hotkey_states.get(hotkey_name, False):
            return  # Prevent multiple triggers if already pressed

        self.hotkey_states[hotkey_name] = True
        self.on_press(hotkey_name)

        # Create an event to monitor the thread's completion
        release_event = threading.Event()
        self.thread_events[hotkey_name] = release_event  # Track this event with the hotkey name

        # Start a background thread to monitor release
        thread = threading.Thread(target=self.monitor_release, args=(hotkey_name, release_event), daemon=True)
        self.active_threads.append(thread)  # Add to active threads list
        print(f"Created thread for {hotkey_name}. Active threads: {len(self.active_threads)}")
        thread.start()

    def monitor_release(self, hotkey_name: str, release_event: threading.Event):
        """Monitors when the hotkey is released and triggers on_release."""
        while keyboard.is_pressed(hotkey_name):
            time.sleep(0.01)  # Avoid excessive CPU usage

        self.hotkey_states[hotkey_name] = False
        self.on_release(hotkey_name)

        # Signal that the thread has finished its task
        release_event.set()

        # Remove the thread from the active threads list when it's done
        self.active_threads = [t for t in self.active_threads if t.is_alive()]  # Keep only alive threads
        print(f"Thread for {hotkey_name} completed. Active threads: {len(self.active_threads)}")

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
            self.can_open_window = True  # Allow reopening window
            return

        # Ensure initial_mouse_pos is not None
        if self.initial_mouse_pos is None:
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

        # Clean up the thread event after the thread has finished
        if hotkey_name in self.thread_events:
            del self.thread_events[hotkey_name]
