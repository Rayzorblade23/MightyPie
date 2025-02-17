import threading
from copy import deepcopy
from threading import Lock
from typing import Dict, Tuple, Set, Optional, Type, List, Any

import win32con
import win32gui
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QKeyEvent, QCursor, QGuiApplication
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView

from data.button_info import ButtonInfo
from data.config import CONFIG
from data.window_manager import WindowManager
from events import ShowWindowEvent, HotkeyReleaseEvent
from gui.buttons.pie_button import PieButton
from gui.menus.pie_menu import PieMenu, PrimaryPieMenu, SecondaryPieMenu
from gui.menus.special_menu import SpecialMenu
from utils.window_utils import get_filtered_list_of_windows, show_special_menu, cache_being_cleared, load_cache


class PieWindow(QMainWindow):
    EXIT_CODE_REBOOT = 122

    # Add a custom signal for thread-safe updates
    update_buttons_signal = pyqtSignal(list)

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
        self.last_window_handles = []
        self.windowHandles_To_buttonIndexes_map = {}
        self.fixed_button_indexes: Set[int] = set()
        self.fixed_windows: Set[int] = set()

        self.active_child = 1
        self.is_window_open = False

        self.initialize_ui()
        self.setup_window()
        self.connect_signals()
        self.auto_refresh()

    # region Initialization and Setup
    def connect_signals(self):
        # Start auto-refreshing every REFRESH_INTERVAL milliseconds
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        self.auto_refresh_timer.start(CONFIG.REFRESH_INTERVAL)  # Periodic refresh
        screen = QApplication.primaryScreen()
        screen.geometryChanged.connect(self.handle_geometry_change)

    def initialize_ui(self):
        """Set up all UI components and data structures."""
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.special_menu = SpecialMenu(obj_name="SpecialMenu", parent=None, main_window=self)
        self.create_pie_menus(CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY, CONFIG.INTERNAL_NUM_PIE_MENUS_SECONDARY)

    def setup_window(self):
        """Set up the main main_window properties."""
        self.setWindowTitle(f"{CONFIG.INTERNAL_PROGRAM_NAME} - Main")
        # Set the default cursor (normal arrow cursor)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # Set the normal cursor
        # Get the primary screen geometry
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        self.setGeometry(0, 0, screen_width, screen_height)
        self.view.setGeometry(0, 0, screen_width, screen_height)
        self.view.setObjectName("PieWindow")
        self.scene.setSceneRect(0, 0, screen_width, screen_height)
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
    def event(self, event):
        """Handle the custom filtered_event to show the main_window."""
        if isinstance(event, ShowWindowEvent):
            pie_menu: PieMenu = event.child_window
            if pie_menu is not None:
                print(f"Showing Pie Menu {pie_menu.pie_menu_index} - {pie_menu.view.objectName()}")
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

    def handle_geometry_change(self):
        screen = QApplication.primaryScreen()
        geometry = screen.geometry()

        # Update the main window size based on the screen geometry
        self.setGeometry(0, 0, geometry.width(), geometry.height())

        # Update the QGraphicsView size to match the new screen size
        self.view.setGeometry(0, 0, geometry.width(), geometry.height())

        # Update the QGraphicsScene size to match the new screen size
        self.scene.setSceneRect(0, 0, geometry.width(), geometry.height())

    def open_special_menu(self):
        if hasattr(self, "special_menu"):
            self.hide()
            show_special_menu(self.special_menu)
        else:
            print("No SpecialMenu here...")

    def refresh(self):
        # Start the background task
        threading.Thread(target=self.update_button_window_assignment, daemon=True).start()

    def auto_refresh(self):
        """Automatically monitor and refresh windows periodically in a thread-safe way."""
        # start_time = time.time()
        # Lock access to shared data to ensure thread safety
        with self.button_mapping_lock:
            current_window_handles = [
                values[0] for values in get_filtered_list_of_windows(self).values()
            ]
            # only actually refresh when windows have opened or closed
            if current_window_handles != self.last_window_handles:
                self.last_window_handles = current_window_handles
                self.refresh()  # Safely call the refresh method to update UI

        # elapsed_time = time.time() - start_time
        # print(f"auto_refresh took {elapsed_time:.3f} seconds")

    # endregion

    # region Window Management and Updates
    def update_button_window_assignment(self) -> None:
        """
        Updates button info with current window information.
        Handles both existing window mappings and unassigned windows.
        Thread-safe method called periodically to refresh button states.
        """
        if cache_being_cleared:
            print("Cache is being cleared. Skipping update.")
            return

        # Get window state and application metadata
        open_windows_info: Dict[int, tuple[str, str, int]] = self.manager.get_open_windows_info()
        app_info_cache: Dict[str, Dict[str, str]] = load_cache()

        print(open_windows_info)

        # Create working copy of button configurations
        updated_button_config: Dict[int, Dict[str, Any]] = deepcopy(self.button_info.get_all_tasks())

        # Track processed buttons
        processed_buttons: Set[int] = set()

        # Get filtered button sets by type
        show_program_window_buttons = self.button_info.filter_buttons("task_type", "show_program_window")
        show_any_window_buttons = self.button_info.filter_buttons("task_type", "show_any_window")

        # Process program-specific buttons
        self._update_existing_handles(show_program_window_buttons, open_windows_info, processed_buttons, True)
        self._assign_free_windows_for_show_program_window_buttons(
            show_program_window_buttons, open_windows_info, app_info_cache, processed_buttons)

        # Process generic window buttons
        self._update_existing_handles(show_any_window_buttons, open_windows_info, processed_buttons)
        self._assign_free_windows_for_show_any_window_buttons(
            show_any_window_buttons, open_windows_info, app_info_cache, processed_buttons)

        # Apply updates and refresh UI
        updated_button_config.update(show_any_window_buttons)
        updated_button_config.update(show_program_window_buttons)
        self._emit_button_updates(updated_button_config)

    def _update_existing_handles(
            self,
            buttons: Dict[int, Dict[str, Any]],
            windows_info: Dict[int, tuple[str, str, int]],
            processed_buttons: Set[int] = None,
            is_show_program_button: bool = False
    ) -> None:
        """Checks buttons with existing window handles and clears invalid ones."""
        for button_id, button in buttons.items():
            hwnd: int = button['properties']['window_handle']
            if hwnd in windows_info:
                windows_info.pop(hwnd)
                processed_buttons.add(button_id)
            else:
                if not is_show_program_button:
                    self._clear_button_properties(button)

    def _assign_free_windows_for_show_program_window_buttons(
            self,
            buttons: Dict[int, Dict[str, Any]],
            windows_info: Dict[int, tuple[str, str, int]],
            app_info_cache: Dict[str, Dict[str, str]],
            processed_buttons: Set[int]
    ) -> None:
        """Maps program-specific windows to their designated buttons."""
        for button_id, button in buttons.items():
            if button_id in processed_buttons:
                continue

            exe_name = button['properties']['exe_name']
            if exe_name not in app_info_cache:
                button['properties'].update({
                    'window_handle': -1,
                    'app_name': exe_name.rstrip(".exe").capitalize()
                })
                continue

            matching_window = None
            for hwnd, (window_title, exe_name_from_window, instance_id) in windows_info.items():
                if exe_name_from_window == exe_name:
                    windows_info.pop(hwnd)
                    matching_window = (hwnd, window_title, exe_name_from_window, instance_id)
                    processed_buttons.add(button_id)
                    break

            if matching_window:
                hwnd, title, _, instance = matching_window
                button['properties']['window_handle'] = hwnd
                self._update_button_with_window_info(
                    button, title, exe_name, instance, app_info_cache, True)
            else:
                button['properties']['window_handle'] = 0
                self._update_button_with_window_info(
                    button, "", exe_name, 0, app_info_cache, True)

    def _assign_free_windows_for_show_any_window_buttons(
            self,
            buttons: Dict[int, Dict[str, Any]],
            windows_info: Dict[int, tuple[str, str, int]],
            app_info_cache: Dict[str, Dict[str, str]],
            processed_buttons: Set[int]
    ) -> None:
        """Assigns remaining windows to buttons that have no window handle."""
        for button_id, button in buttons.items():
            if button_id in processed_buttons:
                continue

            if button['properties']['window_handle'] == -1 and windows_info:
                hwnd, (title, exe_name, instance) = windows_info.popitem()
                button['properties']['window_handle'] = hwnd
                self._update_button_with_window_info(button, title, exe_name, instance, app_info_cache)
                processed_buttons.add(button_id)

    @staticmethod
    def _update_button_with_window_info(
            button: Dict[str, Any],
            title: str,
            exe_name: str,
            instance: int,
            app_info_cache: Dict[str, Dict[str, str]],
            include_exe_path: bool = False
    ) -> None:
        """Updates button properties with window information and app cache data."""
        button['properties'].update({
            'window_title': f"{title} ({instance})" if instance != 0 else title,
            'app_name': app_info_cache.get(exe_name, {}).get('app_name', ''),
            'app_icon_path': app_info_cache.get(exe_name, {}).get('icon_path', ''),
            **({'exe_path': app_info_cache.get(exe_name, {}).get('exe_path', '')} if include_exe_path else {})
        })

    @staticmethod
    def _clear_button_properties(button: Dict[str, Any]) -> None:
        """Clears all properties of a button."""
        button['properties'].update({
            'window_handle': -1,
            'window_title': '',
            'app_name': '',
            'app_icon_path': '',
        })

    def _emit_button_updates(self, updated_config: Dict[int, Dict[str, Any]]) -> None:
        """Emits button updates to all pie menus."""
        for pie_menu in self.pie_menus_primary + self.pie_menus_secondary:
            pie_menu.update_buttons_signal.emit(updated_config)

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
            print(f"Warning: Invalid pie_menu_type: {pie_menu_type}")
            return None, None

        if not pie_menus or not isinstance(pie_menus, list):
            print(f"Warning: {menu_type_str.replace('_', ' ').title()} Pie Menus are not instantiated.")
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

        print("Active child index is out of range for task switchers.")
        return None

    def clean_up_stale_window_mappings(self, final_button_updates):
        # Clean up stale window mappings
        if len(self.windowHandles_To_buttonIndexes_map) > 40:
            valid_handles = {update["properties"]["window_handle"] for update in final_button_updates}
            self.windowHandles_To_buttonIndexes_map = {
                handle: button_id
                for handle, button_id in self.windowHandles_To_buttonIndexes_map.items()
                if handle in valid_handles
            }

    def show_pie_menu_at_mouse_pos(self, pie_menu):
        """Display the main window and bring it to the foreground."""
        try:
            # get Pie Window handle
            hwnd = int(self.winId())
            cursor_pos = QCursor.pos()
            screen, screen_geometry = self.get_screen_bounds(cursor_pos)
            corrected_x, corrected_y = self.calculate_corrected_pie_menu_position(cursor_pos, pie_menu, screen_geometry)

            if pie_menu:
                pie_menu.move(corrected_x, corrected_y)

            self.adjust_pie_window_to_screen(screen_geometry)

            # prevent flicker at the last Pie Menu Position
            self.setWindowOpacity(0)
            self.show()
            QTimer.singleShot(1, lambda: self.setWindowOpacity(1))

            self.get_pie_window_to_foreground(hwnd)

            return cursor_pos

        except Exception as e:
            print(f"Error showing the main window: {e}")

    def adjust_pie_window_to_screen(self, screen_geometry):
        self.move(screen_geometry.topLeft())
        self.setFixedSize(screen_geometry.width(), screen_geometry.height())
        self.view.setFixedSize(screen_geometry.width(), screen_geometry.height())
        self.scene.setSceneRect(0, 0, screen_geometry.width(), screen_geometry.height())

    @staticmethod
    def get_screen_bounds(cursor_pos):
        """Retrieve the screen and its available geometry based on the cursor position."""
        screen = QGuiApplication.screenAt(cursor_pos)
        screen_geometry = screen.availableGeometry()
        return screen, screen_geometry

    @staticmethod
    def calculate_corrected_pie_menu_position(cursor_pos, pie_menu, screen_geometry):
        """Calculate the corrected position for the pie menu to ensure it stays within screen bounds."""
        screen_left, screen_top = screen_geometry.left(), screen_geometry.top()
        screen_right, screen_bottom = screen_geometry.right(), screen_geometry.bottom()

        new_x = max(screen_left, min(cursor_pos.x() - (pie_menu.width() // 2), screen_right - pie_menu.width()))
        new_y = max(screen_top, min(cursor_pos.y() - (pie_menu.height() // 2), screen_bottom - pie_menu.height()))

        return new_x - screen_left, new_y - screen_top

    @staticmethod
    def get_pie_window_to_foreground(hwnd):
        """Bring the pie window to the foreground and ensure it stays on top momentarily."""
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        for flag in [win32con.HWND_NOTOPMOST, win32con.HWND_TOPMOST, win32con.HWND_NOTOPMOST]:
            win32gui.SetWindowPos(hwnd, flag, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
    # endregion
