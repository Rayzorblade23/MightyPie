import logging
import threading
from threading import Lock
from typing import Dict, Tuple, Optional, Type, List

import win32con
import win32gui
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, pyqtSlot
from PyQt6.QtGui import QKeyEvent, QCursor, QGuiApplication, QScreen
from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsView

from src.data.button_info import ButtonInfo
from src.data.config import CONFIG
from src.data.window_manager import WindowManager
from src.events import ShowWindowEvent, HotkeyReleaseEvent
from src.gui.buttons.pie_button import PieButton
from src.gui.menus.pie_menu import PieMenu, PrimaryPieMenu, SecondaryPieMenu
from src.gui.menus.special_menu import SpecialMenu
from src.utils.program_utils import restart_program, get_active_setup_screen, get_screen_dpi
from src.utils.window_utils import get_filtered_list_of_windows, load_cache, update_icon_paths_in_cache

logger = logging.getLogger(__name__)


class PieWindow(QMainWindow):
    EXIT_CODE_REBOOT = 122

    # Add a custom signal for thread-safe updates
    update_buttons_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.scene: Optional[QGraphicsScene] = None
        self.view: Optional[QGraphicsView] = None
        self.special_menu: Optional[SpecialMenu] = None
        self.pie_menus_primary: Optional[List[PieMenu]] = None
        self.pie_menus_secondary: Optional[List[PieMenu]] = None
        self.auto_refresh_timer: Optional[QTimer] = None

        self.manager = WindowManager.get_instance()
        self.button_info: ButtonInfo = ButtonInfo.get_instance()

        self.pie_menu_pos = QPoint()
        self.button_mapping_lock = Lock()

        self.primary_screen: QScreen = get_active_setup_screen()
        self.last_dpi: float = get_screen_dpi(self.primary_screen)

        self.active_child = 1
        self.is_window_open = False
        self.cursor_displacement = (0, 0)  # Track how much the cursor has been moved

        # Check if the icons still exist, otherwise delete entries so they can update again
        update_icon_paths_in_cache()

        self.initialize_ui()
        self.setup_window()
        self.connect_signals()
        self.auto_refresh()

    # region Initialization and Setup
    def connect_signals(self):
        self.update_buttons_signal.connect(self.update_button_ui)

        # Start auto-refreshing every REFRESH_INTERVAL milliseconds
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        self.auto_refresh_timer.timeout.connect(self.handle_monitor_setup_change)
        self.auto_refresh_timer.start(CONFIG.REFRESH_INTERVAL)  # Periodic refresh

    def initialize_ui(self):
        """Set up all UI components and data structures."""
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.special_menu = SpecialMenu(obj_name="SpecialMenu", parent=None)
        self.create_pie_menus(CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY, CONFIG.INTERNAL_NUM_PIE_MENUS_SECONDARY)

    def setup_window(self):
        """Set up the main main_window properties."""
        self.setWindowTitle(f"{CONFIG.INTERNAL_PROGRAM_NAME} - Main")
        # Set the default cursor (normal arrow cursor)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # Set the normal cursor

        self.view.setObjectName("PieWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def create_pie_menus(self, num_primary: int, num_secondary: int) -> None:
        """Creates primary and secondary pie menus and appends them to respective lists."""
        self.pie_menus_primary = [
            PrimaryPieMenu(i, "PrimaryPieMenu", parent=self)
            for i in range(num_primary)
        ]

        self.pie_menus_secondary = [
            SecondaryPieMenu(num_primary + i, "SecondaryPieMenu", parent=self)
            for i in range(num_secondary)
        ]

    # endregion

    # region Event Handling
    def handle_monitor_setup_change(self):
        """Detect DPI changes and restart the UI."""
        new_screen: QScreen = get_active_setup_screen()
        new_dpi = get_screen_dpi(new_screen)

        if new_dpi != self.last_dpi:
            logger.info(f"DPI change detected: {self.last_dpi} -> {new_dpi}. Restarting program...")
            restart_program()

    def event(self, event):
        """Handle the custom filtered_event to show the main_window."""
        if isinstance(event, ShowWindowEvent):
            pie_menu: PieMenu = event.child_window
            if pie_menu is not None:
                # Hide siblings of class PieMenuTaskSwitcher
                for sibling in self.children():
                    if sibling is not pie_menu and isinstance(sibling, PieMenu):
                        sibling.hide()
                pie_menu.show()
                if "Task" in pie_menu.view.objectName():
                    self.refresh()
                self.pie_menu_pos = self.show_pie_menu_at_mouse_pos(
                    pie_menu)  # Safely call show_pie_menu_at_mouse_pos when the filtered_event is posted
            return True
        elif isinstance(event, HotkeyReleaseEvent):
            pie_menu = event.child_window
            pie_buttons: Dict[int, PieButton]  # Where 'SomeType' is the type of items in pie_buttons

            # If there's an active section, click that button
            if hasattr(pie_menu.area_button, 'current_active_section'):
                active_section = pie_menu.area_button.current_active_section
                if active_section != -1:
                    pie_menu.pie_buttons[active_section].trigger_left_click_action()
            self.hide()
            return True
        return super().event(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Close the main_window on pressing the Escape key."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)  # Pass other key events to the

    def closeEvent(self, event):
        """Hide the main_window instead of closing it."""
        self.hide()
        event.ignore()  # Prevent the default close behavior

    def open_special_menu(self):
        if hasattr(self, "special_menu"):
            self.special_menu.show_menu()
            self.hide()
        else:
            logger.error("No SpecialMenu here...")

    def refresh(self, reassign_all_buttons: bool = False):
        # Start the background task
        app_info_cache = load_cache()
        self.manager.set_app_info_cache(app_info_cache)

        # Create a method that wraps the thread's work
        def update_thread_wrapper():
            try:
                self.manager.update_button_window_assignment(
                    self, self.button_info, reassign_all_buttons
                )
            except Exception as e:
                logger.error(f"Error in update_button_window_assignment thread: {e}", exc_info=True)

        # Start the thread with the wrapper
        threading.Thread(
            target=update_thread_wrapper,
            daemon=True,
            name="ButtonWindowAssignmentThread"
        ).start()

    def auto_refresh(self):
        """Automatically monitor and refresh windows periodically in a thread-safe way."""
        # from pyinstrument import Profiler
        #
        # profiler = Profiler()
        # profiler.start()

        # Lock access to shared data to ensure thread safety
        with self.button_mapping_lock:
            current_window_handles = [
                values[0] for values in get_filtered_list_of_windows(self).values()
            ]
            # Compare against WindowManager's last_window_handles
            if current_window_handles != self.manager.last_window_handles:
                self.manager.last_window_handles = current_window_handles
                self.refresh()

        # # Stop profiling
        # profiler.stop()
        #
        # # Output the results (text format with color)
        # print(profiler.output_text(unicode=True, color=True))

    def force_refresh(self, reassign_all_buttons: bool = False):
        """Automatically monitor and refresh windows periodically in a thread-safe way."""
        with self.button_mapping_lock:
            current_window_handles = [
                values[0] for values in get_filtered_list_of_windows(self).values()
            ]
            self.manager.last_window_handles = current_window_handles
            self.refresh(reassign_all_buttons)

    @pyqtSlot(dict)
    def update_button_ui(self, updated_button_config):
        # Save updates to global Button Info
        self.button_info.button_info_dict = updated_button_config

        self.button_info.has_unsaved_changes = True
        self.button_info.save_to_json()

        for pie_menu in self.pie_menus_primary + self.pie_menus_secondary:
            pie_menu.update_button_ui(updated_button_config)

    # endregion

    # region Pie Menu Navigation and Display
    def get_next_pie_menu_on_hotkey_press(self, pie_menu_type: Type[PieMenu]) -> Tuple[Optional[PieMenu], Optional[int]]:
        """Helper to find the next pie menu (task switcher or window control) to toggle.

        Args:
            pie_menu_type: The class type (PrimaryPieMenu or SecondaryPieMenu) of pie menu to search for.

        Returns:
            A tuple containing the next child window to activate and its corresponding
            main_window_active_child index.  Returns (None, None) if an error occurs
            or the specified menu type is invalid.
        """

        if pie_menu_type is PrimaryPieMenu:
            pie_menus = self.pie_menus_primary
            offset = 0  # Task switchers start at index 1 in main_window_active_child
            menu_type_str = "primary"  # string of pie_menu for error printing
        elif pie_menu_type is SecondaryPieMenu:
            pie_menus = self.pie_menus_secondary
            pie_menus_primary = self.pie_menus_primary
            offset = CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY if pie_menus_primary else 0
            menu_type_str = "secondary"  # string of pie_menu for error printing
        else:
            logger.error(f"Warning: Invalid pie_menu_type: {pie_menu_type}")
            return None, None

        if not pie_menus or not isinstance(pie_menus, list):
            logger.error(f"Warning: {menu_type_str.replace('_', ' ').title()} Pie Menus are not instantiated.")
            return None, None

        # Find the first pie menu to toggle or open the next one
        for index, current_pie_menu in enumerate(pie_menus):
            if current_pie_menu.isVisible():
                # Toggle to the next pie menu or back to the first
                next_index = (index + 1) % len(pie_menus)
                pie_menu = pie_menus[next_index]
                main_window_active_child = offset + next_index + 1
                return pie_menu, main_window_active_child
        else:
            # If none are visible, open the first pie menu
            pie_menu = pie_menus[0]
            main_window_active_child = offset + 1
            return pie_menu, main_window_active_child

    def get_pie_menu_after_hotkey_drag(self, pie_menu_type: type[PieMenu]) -> PieMenu | None:
        """Selects the appropriate pie menu based on active_child and menu type."""
        if pie_menu_type is PrimaryPieMenu:
            offset = 0
            menus = self.pie_menus_primary
        elif pie_menu_type is SecondaryPieMenu:
            offset = CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY
            menus = self.pie_menus_secondary
        else:
            raise ValueError("Invalid pie_menu_type. Expected PrimaryPieMenu or SecondaryPieMenu.")

        index = self.active_child - 1 - offset

        if 0 <= index < CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY:
            return menus[index]

        logger.error("Active child index is out of range for task switchers.")
        return None

    def show_pie_menu_at_mouse_pos(self, pie_menu):
        """Display the pie menu at the corrected position near the cursor."""
        try:
            # Get the Pie Window handle and cursor position
            hwnd = int(self.winId())
            global_cursor_pos = QCursor.pos()

            screen, screen_geometry = self.get_screen_bounds(global_cursor_pos)

            # Calculate the cursor position relative to the screen
            cursor_pos = global_cursor_pos - screen_geometry.topLeft()

            # Calculate the corrected position for the pie menu
            corrected_x, corrected_y = self.calculate_corrected_pie_menu_position(cursor_pos, pie_menu, screen_geometry)

            # Move the pie menu to the calculated corrected position
            pie_menu.move(corrected_x, corrected_y)

            # Calculate the cursor center position relative to the screen
            pie_menu_center_x = corrected_x + pie_menu.width() // 2
            pie_menu_center_y = corrected_y + pie_menu.height() // 2

            # Store the cursor displacement
            self.cursor_displacement = (
                pie_menu_center_x - cursor_pos.x(),
                pie_menu_center_y - cursor_pos.y()
            )

            # Teleport the cursor to the center of the pie menu
            QCursor.setPos(screen_geometry.x() + pie_menu_center_x, screen_geometry.y() + pie_menu_center_y)

            # Adjust the pie menu to the screen's bounds and display it
            self.adjust_pie_window_to_screen(screen_geometry)

            # Show the pie menu with fading effect
            self.setWindowOpacity(0)
            self.show()
            QTimer.singleShot(1, lambda: self.setWindowOpacity(1))

            self.get_pie_window_to_foreground(hwnd)

            logger.debug(f"Pie menu displayed at ({corrected_x}, {corrected_y})")

            return cursor_pos

        except Exception as e:
            logger.error(f"Error showing the pie menu: {e}")
            return None

    def adjust_pie_window_to_screen(self, screen_geometry) -> None:
        """Adjust the pie window to fit the screen geometry."""
        # Accessing the integer values from QRect
        self.setGeometry(screen_geometry)

        self.view.setGeometry(0, 0, self.geometry().width(), self.geometry().height())
        self.scene.setSceneRect(0, 0, self.geometry().width(), self.geometry().height())

    @staticmethod
    def get_screen_bounds(cursor_pos):
        """Retrieve the screen and its available geometry based on the cursor position."""
        screen = QGuiApplication.screenAt(cursor_pos)
        return screen, screen.availableGeometry()

    @staticmethod
    def calculate_corrected_pie_menu_position(cursor_pos, pie_menu, screen_geometry):
        """Calculate the corrected position for the pie menu to ensure it stays within screen bounds."""
        # Center pie menu on cursor
        desired_x = cursor_pos.x() - (pie_menu.width() // 2)
        desired_y = cursor_pos.y() - (pie_menu.height() // 2)

        # Calculate screen boundaries
        screen_right = screen_geometry.width()
        screen_bottom = screen_geometry.height()

        # Clamp to screen bounds
        new_x = max(0, min(desired_x, screen_right - pie_menu.width()))
        new_y = max(0, min(desired_y, screen_bottom - pie_menu.height()))

        # Log if position needed to be adjusted
        if new_x != desired_x or new_y != desired_y:
            logger.debug("Pie menu position adjusted to fit screen boundaries")

        return new_x, new_y

    @staticmethod
    def get_pie_window_to_foreground(hwnd):
        """Bring the pie window to the foreground and ensure it stays on top momentarily."""
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
            # Brief delay to ensure visibility then reset topmost state
            QTimer.singleShot(100, lambda: win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_NOTOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            ))
        except Exception as e:
            logger.warning(f"Failed to bring window to foreground: {e}")
    # endregion
