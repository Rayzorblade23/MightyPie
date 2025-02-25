import threading
from threading import Lock
from typing import Dict, Tuple, Optional, Type, List

import win32con
import win32gui
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QRect
from PyQt6.QtGui import QKeyEvent, QCursor, QGuiApplication
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView

from data.button_info import ButtonInfo
from data.config import CONFIG
from data.window_manager import WindowManager
from events import ShowWindowEvent, HotkeyReleaseEvent
from gui.buttons.pie_button import PieButton
from gui.menus.pie_menu import PieMenu, PrimaryPieMenu, SecondaryPieMenu
from gui.menus.special_menu import SpecialMenu
from utils.window_utils import get_filtered_list_of_windows, load_cache


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
        self.button_info = ButtonInfo.get_instance()

        self.pie_menu_pos = QPoint()
        self.button_mapping_lock = Lock()

        self.active_child = 1
        self.is_window_open = False
        self.cursor_displacement = (0, 0)  # Track how much the cursor has been moved

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
        self.special_menu = SpecialMenu(obj_name="SpecialMenu", parent=None)
        self.create_pie_menus(CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY, CONFIG.INTERNAL_NUM_PIE_MENUS_SECONDARY)

    def setup_window(self):
        """Set up the main main_window properties."""
        self.setWindowTitle(f"{CONFIG.INTERNAL_PROGRAM_NAME} - Main")
        # Set the default cursor (normal arrow cursor)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # Set the normal cursor
        # Get the combined geometry of all screens
        virtual_geometry = self._get_virtual_geometry()

        # Set the position and size to cover all screens
        self.setGeometry(virtual_geometry)
        self.view.setGeometry(0, 0, virtual_geometry.width(), virtual_geometry.height())
        self.scene.setSceneRect(0, 0, virtual_geometry.width(), virtual_geometry.height())

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
    def event(self, event):
        """Handle the custom filtered_event to show the main_window."""
        if isinstance(event, ShowWindowEvent):
            pie_menu: PieMenu = event.child_window
            if pie_menu is not None:
                # print(f"Showing Pie Menu {pie_menu.pie_menu_index} - {pie_menu.view.objectName()}")
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
        # Get the combined geometry of all screens
        virtual_geometry = self._get_virtual_geometry()

        # Update the main window size based on the screen geometry
        self.setGeometry(virtual_geometry)

        # Update the QGraphicsView size to match the new screen size
        self.view.setGeometry(0, 0, virtual_geometry.width(), virtual_geometry.height())

        # Update the QGraphicsScene size to match the new screen size
        self.scene.setSceneRect(0, 0, virtual_geometry.width(), virtual_geometry.height())


    @staticmethod
    def _get_virtual_geometry():
        """Calculate the bounding rectangle that contains all screens."""
        # Start with an empty rectangle
        virtual_geometry = QRect()

        # Iterate through all screens and unite their geometries
        for screen in QApplication.screens():
            screen_geo = screen.geometry()
            if virtual_geometry.isEmpty():
                virtual_geometry = screen_geo
            else:
                virtual_geometry = virtual_geometry.united(screen_geo)

        return virtual_geometry

    def open_special_menu(self):
        if hasattr(self, "special_menu"):
            self.special_menu.show_menu()
            self.hide()
        else:
            print("No SpecialMenu here...")

    def refresh(self, reassign_all_buttons: bool = False):
        # Start the background task
        app_info_cache = load_cache()
        self.manager.set_app_info_cache(app_info_cache)

        threading.Thread(
            target=self.manager.update_button_window_assignment(
                self, self.button_info, reassign_all_buttons
            ),
            daemon=True
        ).start()

    def auto_refresh(self):
        """Automatically monitor and refresh windows periodically in a thread-safe way."""
        # start_time = time.time()
        # Lock access to shared data to ensure thread safety
        with self.button_mapping_lock:
            current_window_handles = [
                values[0] for values in get_filtered_list_of_windows(self).values()
            ]
            # Compare against WindowManager's last_window_handles
            if current_window_handles != self.manager.last_window_handles:
                self.manager.last_window_handles = current_window_handles
                self.refresh()

        # elapsed_time = time.time() - start_time
        # print(f"auto_refresh took {elapsed_time:.3f} seconds")

    def force_refresh(self, reassign_all_buttons: bool = False):
        """Automatically monitor and refresh windows periodically in a thread-safe way."""
        with self.button_mapping_lock:
            current_window_handles = [
                values[0] for values in get_filtered_list_of_windows(self).values()
            ]
            self.manager.last_window_handles = current_window_handles
            self.refresh(reassign_all_buttons)

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

    def show_pie_menu_at_mouse_pos(self, pie_menu):
        """Display the pie menu at the corrected position near the cursor."""
        try:
            # Get the Pie Window handle and cursor position
            hwnd = int(self.winId())
            cursor_pos = QCursor.pos()

            screen, screen_geometry = self.get_screen_bounds(cursor_pos)

            virtual_geometry = self._get_virtual_geometry()

            # Calculate the corrected position for the pie menu and move it
            corrected_x, corrected_y = self.calculate_corrected_pie_menu_position(cursor_pos, pie_menu, screen_geometry)

            # Ensure that the corrected position is relative to the current screen
            corrected_x += screen_geometry.left()
            corrected_y += screen_geometry.top()

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
            QCursor.setPos(pie_menu_center_x, pie_menu_center_y)

            # Adjust the pie menu to the screen's bounds and display it
            self.adjust_pie_window_to_screen(virtual_geometry)
            self.setWindowOpacity(0)
            self.show()
            QTimer.singleShot(1, lambda: self.setWindowOpacity(1))

            self.get_pie_window_to_foreground(hwnd)

            return cursor_pos

        except Exception as e:
            print(f"Error showing the pie menu: {e}")

    def adjust_pie_window_to_screen(self, virtual_geometry):
        """Adjust the pie window to fit the screen geometry."""
        self.setGeometry(virtual_geometry)
        self.view.setGeometry(virtual_geometry)
        self.scene.setSceneRect(0, 0, virtual_geometry.width(), virtual_geometry.height())


    @staticmethod
    def get_screen_bounds(cursor_pos):
        """Retrieve the screen and its available geometry based on the cursor position."""
        screen = QGuiApplication.screenAt(cursor_pos)
        return screen, screen.availableGeometry()

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
