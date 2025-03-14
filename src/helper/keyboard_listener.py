import logging
import time
from typing import TYPE_CHECKING

import keyboard
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication

from src.data.config import CONFIG
from src.events import ShowWindowEvent, HotkeyReleaseEvent
from src.gui.menus.pie_menu import PrimaryPieMenu, SecondaryPieMenu

if TYPE_CHECKING:
    from src.gui.pie_window import PieWindow

# Create a module-specific logger
logger = logging.getLogger(__name__)


class HotkeyListener:
    def __init__(self, main_window: 'PieWindow'):
        """Initializes the HotkeyListener with a reference to the main window."""
        self.main_window = main_window
        self.can_open_window = True  # Track window state
        self.initial_mouse_pos = None  # Store initial mouse position on press
        self.is_hotkey_pressed = False  # Flag to suppress auto-repeat

        self.hotkey_mapping, self.hotkey_keys = self.create_hotkey_mapping()  # Pre-load the mapping

        logger.info("HotkeyListener initialized")

    def start_listening(self):
        """Starts listening for the configured hotkeys."""
        logger.info(f"Starting hotkey listener with hotkeys: primary={CONFIG.HOTKEY_PRIMARY}, secondary={CONFIG.HOTKEY_SECONDARY}")

        try:
            # Register hotkeys for press events
            keyboard.add_hotkey(CONFIG.HOTKEY_PRIMARY, self.handle_press, args=(CONFIG.HOTKEY_PRIMARY,), suppress=True)
            keyboard.add_hotkey(CONFIG.HOTKEY_SECONDARY, self.handle_press, args=(CONFIG.HOTKEY_SECONDARY,), suppress=True)

            # Register release handlers for only the last key of the hotkey
            keyboard.on_release_key(self.get_last_key(CONFIG.HOTKEY_PRIMARY), lambda _: self.handle_release(CONFIG.HOTKEY_PRIMARY))
            keyboard.on_release_key(self.get_last_key(CONFIG.HOTKEY_SECONDARY), lambda _: self.handle_release(CONFIG.HOTKEY_SECONDARY))

            # Keep the program running
            while True:
                time.sleep(0.1)  # Prevent busy waiting

        except Exception as e:
            logger.error(f"Failed to register hotkeys: {e}", exc_info=True)

    def pause_listening(self):
        """Temporarily disables hotkey listening."""
        logger.info("Pausing hotkey listener...")
        try:
            keyboard.unhook_all_hotkeys()  # Only unhook hotkeys, not all keyboard handlers
            self.can_open_window = False
            logger.info("Hotkey listener paused")
        except Exception as e:
            logger.error(f"Error during hotkey pause: {e}", exc_info=True)

    def resume_listening(self):
        """Resumes hotkey listening after being paused."""
        logger.info("Resuming hotkey listener...")
        try:
            # Re-register hotkeys for press events
            keyboard.add_hotkey(CONFIG.HOTKEY_PRIMARY, self.handle_press, args=(CONFIG.HOTKEY_PRIMARY,), suppress=True)
            keyboard.add_hotkey(CONFIG.HOTKEY_SECONDARY, self.handle_press, args=(CONFIG.HOTKEY_SECONDARY,), suppress=True)
            self.can_open_window = True
            logger.info("Hotkey listener resumed")
        except Exception as e:
            logger.error(f"Error during hotkey resume: {e}", exc_info=True)

    def handle_press(self, hotkey_name: str):
        """Handles hotkey press events."""
        if not self.can_open_window:
            logger.debug(f"Hotkey '{hotkey_name}' press ignored (already active).")
            return  # Only show if not already open

        logger.debug(f"Hotkey '{hotkey_name}' pressed. Starting handling process.")

        self.initial_mouse_pos = QCursor.pos()  # Store initial mouse position using QCursor

        try:
            if hotkey_name == CONFIG.HOTKEY_PRIMARY:
                pie_menu, main_window_active_child = self.main_window.get_next_pie_menu_on_hotkey_press(PrimaryPieMenu)
                self.main_window.active_child = main_window_active_child
            elif hotkey_name == CONFIG.HOTKEY_SECONDARY:
                pie_menu, main_window_active_child = self.main_window.get_next_pie_menu_on_hotkey_press(SecondaryPieMenu)
                self.main_window.active_child = main_window_active_child
            else:
                logger.warning(f"Unknown hotkey: {hotkey_name}")
                return

            if pie_menu:
                show_event = ShowWindowEvent(self.main_window, pie_menu)
                QApplication.postEvent(self.main_window, show_event)
                self.can_open_window = False
        except Exception as e:
            logger.error(f"Error handling hotkey press '{hotkey_name}': {e}", exc_info=True)
            self.can_open_window = True

    def handle_release(self, hotkey_name: str):
        """Handles hotkey release events."""
        if self.main_window.cursor_displacement is None:
            self.can_open_window = True  # Allow reopening window
            return

        logger.debug(f"Hotkey '{hotkey_name}' released. Processing release.")

        if self.initial_mouse_pos is None:
            return

        current_mouse_pos = QCursor.pos()

        displacement_x = current_mouse_pos.x() - self.initial_mouse_pos.x() - self.main_window.cursor_displacement[0]
        displacement_y = current_mouse_pos.y() - self.initial_mouse_pos.y() - self.main_window.cursor_displacement[1]

        # If the displacement is below the threshold, it's considered a click, not a drag
        if abs(displacement_x) <= 35 and abs(displacement_y) <= 35:
            self.can_open_window = True
        else:
            if hotkey_name == CONFIG.HOTKEY_PRIMARY:
                pie_menu = self.main_window.get_pie_menu_after_hotkey_drag(PrimaryPieMenu)
            elif hotkey_name == CONFIG.HOTKEY_SECONDARY:
                pie_menu = self.main_window.get_pie_menu_after_hotkey_drag(SecondaryPieMenu)
            else:
                logger.warning(f"Unknown hotkey: {hotkey_name}")
                return

            if pie_menu:
                release_event = HotkeyReleaseEvent(self.main_window, pie_menu)
                QApplication.postEvent(self.main_window, release_event)
                self.can_open_window = True

        self.clear_keyboard_state()

    def clear_keyboard_state(self) -> None:
        """Clears the keyboard state only if no hotkey keys are still pressed."""
        try:
            pressed_keys = set(keyboard._pressed_events.keys())  # Get currently pressed scancodes

            # Use pre-loaded mapping
            def scancode_to_name(scancode: int) -> str:
                """Returns a human-friendly key name for a given scancode."""
                return self.hotkey_mapping.get(scancode, f"Unknown({scancode})")

            pressed_keys_human = {scancode_to_name(sc) for sc in pressed_keys}

            # Use human-friendly key names for logging
            hotkey_keys_human = {scancode_to_name(sc) for sc in self.hotkey_keys}

            logger.debug(f"Pressed keys: {', '.join(pressed_keys_human)}")
            logger.debug(f"Hotkey keys: {', '.join(hotkey_keys_human)}")

            if not pressed_keys & self.hotkey_keys:  # No hotkey keys are pressed
                logger.debug("No hotkey keys are currently pressed. Clearing keyboard state.")
                keyboard._pressed_events.clear()
            else:
                remaining_keys = pressed_keys & self.hotkey_keys
                remaining_keys_human = {scancode_to_name(sc) for sc in remaining_keys}
                logger.debug(f"Hotkey keys still pressed, not clearing keyboard state. Remaining: {', '.join(remaining_keys_human)}")

        except Exception as e:
            logger.error("Failed to clear keyboard state: %s", e, exc_info=True)

    @staticmethod
    def stop_listening():
        """Stops the hotkey listener and cleans up resources."""
        logger.info("Stopping hotkey listener...")

        try:
            keyboard.unhook_all()
        except Exception as e:
            logger.error(f"Error during hotkey unhook: {e}", exc_info=True)

        logger.info("Hotkey listener stopped.")

    @staticmethod
    def create_hotkey_mapping() -> tuple[dict[int, str], set[int]]:
        """Creates a mapping of scancodes to human-readable key names for hotkeys."""
        hotkey_keys: set[int] = set()
        hotkey_mapping: dict[int, str] = {}

        # Define the list of hotkeys to handle
        for hotkey in (CONFIG.HOTKEY_PRIMARY, CONFIG.HOTKEY_SECONDARY):
            for key in hotkey.split('+'):
                scancodes = keyboard.key_to_scan_codes(key)
                if scancodes:
                    hotkey_keys.update(scancodes)
                    for sc in scancodes:
                        hotkey_mapping[sc] = key

        # Return the mappings: human-readable names (hotkey_mapping) and set of scancodes (hotkey_keys)
        return hotkey_mapping, hotkey_keys

    @staticmethod
    def get_last_key(hotkey: str) -> str:
        """Extracts the last key from a multi-key hotkey combination."""
        return hotkey.split('+')[-1]  # Extracts "d" from "ctrl+d"
