import logging
import threading
import time
from typing import TYPE_CHECKING

import keyboard
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication, QWidget

from src.data.config import CONFIG
from src.events import ShowWindowEvent, HotkeyReleaseEvent
from src.gui.menus.pie_menu import PrimaryPieMenu, SecondaryPieMenu

if TYPE_CHECKING:
    from src.gui.pie_window import PieWindow

# Create a module-specific logger
logger = logging.getLogger(__name__)


class HotkeyListener:
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

        self._stop_event = threading.Event()  # Event to gracefully stop the listener

        # Simplified thread tracking
        self._release_threads = []
        self._threads_lock = threading.Lock()

        logger.info("HotkeyListener initialized")

        # Start heartbeat logging
        self.start_heartbeat()

    def start_heartbeat(self):
        """Periodically logs a heartbeat to detect silent crashes."""
        def heartbeat():
            while not self._stop_event.is_set():
                logger.debug(f"<3 Heartbeat: HotkeyListener is still running. Can open Window is {self.can_open_window}")
                time.sleep(5)  # Adjust interval if needed

        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()

    def handle_press(self, hotkey_name: str):
        """Handles hotkey press and starts a release monitor if needed."""
        logger.debug(f"Hotkey '{hotkey_name}' pressed. Starting handling process.")

        # Extensive logging for diagnostics
        logger.debug(f"Current hotkey states: {self.hotkey_states}")
        logger.debug(f"Can open window: {self.can_open_window}")

        # Check if hotkey is already in a pressed state
        if self.hotkey_states.get(hotkey_name, False):
            logger.warning(f"Hotkey {hotkey_name} already in pressed state. Skipping.")
            return

        # Reset the state before processing
        self.hotkey_states[hotkey_name] = True

        try:
            self.on_press(hotkey_name)
        except Exception as e:
            logger.error(f"Error in on_press for {hotkey_name}: {e}", exc_info=True)
            # Reset state to allow future hotkey presses
            self.hotkey_states[hotkey_name] = False
            return

        # Simple release monitoring without complex thread management
        def release_monitor():
            try:
                # Wait for key release
                while keyboard.is_pressed(hotkey_name):
                    time.sleep(0.01)  # Avoid excessive CPU usage

                logger.debug(f"Hotkey '{hotkey_name}' released. Triggering on_release.")

                # Reset hotkey state
                self.hotkey_states[hotkey_name] = False
                self.on_release(hotkey_name)
            except Exception as e:
                logger.error(f"Error in release monitoring for {hotkey_name}: {e}", exc_info=True)
                # Ensure hotkey state is reset
                self.hotkey_states[hotkey_name] = False

        def wrapped_release_monitor():
            try:
                release_monitor()
            except Exception as e:
                logger.critical(f"Unhandled exception in release monitor: {e}", exc_info=True)

        release_thread = threading.Thread(target=wrapped_release_monitor, daemon=True)
        release_thread.start()

    def start_listening(self):
        """Starts listening for the configured hotkeys."""
        logger.info(f"Starting hotkey listener with hotkeys: primary={CONFIG.HOTKEY_PRIMARY}, secondary={CONFIG.HOTKEY_SECONDARY}")

        try:
            # Listen for press and trigger on_press
            keyboard.add_hotkey(CONFIG.HOTKEY_PRIMARY,
                                lambda: self.handle_press(CONFIG.HOTKEY_PRIMARY),
                                suppress=True)
            keyboard.add_hotkey(CONFIG.HOTKEY_SECONDARY,
                                lambda: self.handle_press(CONFIG.HOTKEY_SECONDARY),
                                suppress=True)

            # Replace blocking wait with a non-blocking loop
            while not self._stop_event.is_set():
                time.sleep(0.1)  # Prevent busy waiting

        except Exception as e:
            logger.error(f"Failed to register hotkeys: {e}", exc_info=True)
        finally:
            # Ensure cleanup
            try:
                keyboard.unhook_all()
            except Exception as cleanup_e:
                logger.error(f"Error during hotkey unhook: {cleanup_e}")

    def on_press(self, hotkey_name: str):
        """Handles hotkey press events."""
        logger.debug("Processing hotkey press: %s", hotkey_name)

        if not self.can_open_window:
            return  # Only show if not already open

        self.initial_mouse_pos = QCursor.pos()  # Store initial mouse position using QCursor

        logger.debug("Initial mouse position: %s", self.initial_mouse_pos)

        try:
            if hotkey_name == CONFIG.HOTKEY_PRIMARY:
                pie_menu, main_window_active_child = self.main_window.get_next_pie_menu_on_hotkey_press(PrimaryPieMenu)
                self.main_window.active_child = main_window_active_child

            elif hotkey_name == CONFIG.HOTKEY_SECONDARY:
                pie_menu, main_window_active_child = self.main_window.get_next_pie_menu_on_hotkey_press(SecondaryPieMenu)
                self.main_window.active_child = main_window_active_child

            else:
                logger.warning("Unknown hotkey: %s", hotkey_name)
                return

            if pie_menu:
                show_event = ShowWindowEvent(self.main_window, pie_menu)
                QApplication.postEvent(self.main_window, show_event)
                self.can_open_window = False
        except Exception as e:
            logger.error("Error handling hotkey press '%s': %s", hotkey_name, e, exc_info=True)
            # Reset window state to prevent lockouts
            self.can_open_window = True

    def on_release(self, hotkey_name: str):
        """Handles hotkey release events."""
        logger.debug("Processing hotkey release: %s", hotkey_name)

        try:
            # Ensure cursor_displacement is valid
            if self.main_window.cursor_displacement is None:
                self.can_open_window = True  # Allow reopening window
                return

            # Ensure initial_mouse_pos is not None
            if self.initial_mouse_pos is None:
                return

            # Get current mouse position
            current_mouse_pos = QCursor.pos()

            logger.debug("Current mouse position: %s", current_mouse_pos)

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
                    logger.warning("Unknown hotkey: %s", hotkey_name)
                    return

                if pie_menu:
                    release_event = HotkeyReleaseEvent(self.main_window, pie_menu)
                    QApplication.postEvent(self.main_window, release_event)
                    self.can_open_window = True  # Reset the state

        except Exception as e:
            logger.error("Error handling hotkey release '%s': %s", hotkey_name, e, exc_info=True)
            self.can_open_window = True  # Reset state to prevent lockouts
