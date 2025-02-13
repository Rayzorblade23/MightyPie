import os
import subprocess
import sys
import threading
import time
from threading import Lock
from typing import Dict, Tuple, Set, Optional

import psutil
import pyautogui
import win32con
import win32gui
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QCoreApplication, QTimer, QObject
from PyQt6.QtGui import QMouseEvent, QKeyEvent, QCursor, QGuiApplication
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QWidget

from gui.buttons.pie_button import PieButton
from data.button_info import ButtonInfo
from data.config import CONFIG
from events import ShowWindowEvent, HotkeyReleaseEvent
from data.icon_paths import EXTERNAL_ICON_PATHS
from functions.window_functions import get_filtered_list_of_windows, load_cache, show_special_menu, toggle_maximize_window_at_cursor, minimize_window_at_cursor, launch_app, \
    cache_being_cleared, restore_last_minimized_window, focus_all_explorer_windows, center_window_at_cursor
from gui.menus.pie_menu import PieMenu, PieMenuType, PrimaryPieMenu, SecondaryPieMenu
from gui.menus.special_menu import SpecialMenu
from data.window_manager import WindowManager

class PieWindow(QMainWindow):
    EXIT_CODE_REBOOT = 122

    # Add a custom signal for thread-safe updates
    update_buttons_signal = pyqtSignal(list)  # Expect QWidget and list

    def __init__(self):
        super().__init__()
        # Set the default cursor (normal arrow cursor)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # Set the normal cursor

        # Create the scene and view for the left part of the screen
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)

        # Get the primary screen geometry
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Set the main_window size to take the full screen
        self.setGeometry(0, 0, screen_width, screen_height)

        # Set the geometry of the QGraphicsView to take the left half
        self.view.setGeometry(0, 0, screen_width, screen_height)
        self.view.setObjectName("PieWindow")
        self.scene.setSceneRect(0, 0, screen_width, screen_height)

        self.setup_window()

        self.manager = WindowManager.get_instance()
        self.button_info: ButtonInfo = ButtonInfo.get_instance()

        self.pie_menu_pos = QPoint()
        self.button_mapping_lock = Lock()
        self.last_window_handles = []
        self.pie_button_texts = ["Empty" for _ in range(CONFIG.INTERNAL_MAX_BUTTONS * CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY)]
        self.windowHandles_To_buttonIndexes_map = {}
        self.fixed_button_indexes: Set[int] = set()
        self.fixed_windows: Set[int] = set()

        self.active_child = 1
        self.is_window_open = False

        num_primary_pie_menus = CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY
        num_secondary_pie_menus = CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY

        # Create Pie Menus with this main_window as parent
        self.pie_menus_primary: list[PieMenu] = []  # List to hold the task switchers
        for i in range(0, num_primary_pie_menus):  # Adjust the range if the number of task switchers changes
            pie_menu = PrimaryPieMenu(i, "PrimaryPieMenu", parent=self)
            if i > 1:  # Hide task switchers 2 and 3 initially
                pie_menu.hide()
            self.pie_menus_primary.append(pie_menu)

        self.pie_menus_secondary: list[PieMenu] = []
        for i in range(0, num_secondary_pie_menus):  # Adjust the range if the number of task switchers changes
            win_control = SecondaryPieMenu(num_primary_pie_menus + i, "SecondaryPieMenu", parent=self)
            win_control.hide()  # Hide all at first
            self.pie_menus_secondary.append(win_control)

        self.setup_window_control_buttons()

        # For now, right-click should always just hide
        for i in range(CONFIG.INTERNAL_MAX_BUTTONS * CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY):
            pie_menu, index = self.get_pie_menu_and_index(i, PieMenuType.TASK_SWITCHER)
            pie_menu.pie_buttons[index].set_right_click_action(action=lambda: self.hide())

        for i in range(CONFIG.INTERNAL_MAX_BUTTONS * CONFIG.INTERNAL_NUM_PIE_MENUS_SECONDARY):
            win_control, index = self.get_pie_menu_and_index(i, PieMenuType.WIN_CONTROL)
            win_control.pie_buttons[index].set_right_click_action(action=lambda: self.hide())

        self.special_menu = SpecialMenu(obj_name="SpecialMenu", parent=None, main_window=self)
        self.special_menu.hide()

        # Start auto-refreshing every REFRESH_INTERVAL milliseconds
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        self.auto_refresh_timer.start(CONFIG.REFRESH_INTERVAL)  # Periodic refresh

        screen = QApplication.primaryScreen()
        screen.geometryChanged.connect(self.handle_geometry_change)

        self.auto_refresh()

    @staticmethod
    def restart_program():
        current_pid = os.getpid()
        print(f"Restarting. Current PID: {current_pid}")

        if hasattr(sys, '_instance'):
            sys._instance.release_for_restart()

        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] != current_pid and proc.info['cmdline']:
                    if sys.argv[0] in proc.info['cmdline']:
                        print(f"Killing old instance: PID {proc.info['pid']}")
                        proc.terminate()
            except psutil.NoSuchProcess:
                pass

        new_process = subprocess.Popen([sys.executable] + sys.argv)
        print(f"New process started with PID: {new_process.pid}")

        time.sleep(1)
        os._exit(0)

    def quit_program(self):
        QCoreApplication.exit()

    def handle_geometry_change(self):
        screen = QApplication.primaryScreen()
        geometry = screen.geometry()

        # Update the main window size based on the screen geometry
        self.setGeometry(0, 0, geometry.width(), geometry.height())

        # Update the QGraphicsView size to match the new screen size
        self.view.setGeometry(0, 0, geometry.width(), geometry.height())

        # Update the QGraphicsScene size to match the new screen size
        self.scene.setSceneRect(0, 0, geometry.width(), geometry.height())

    def closeEvent(self, event):
        """Hide the main_window instead of closing it."""
        self.hide()
        event.ignore()  # Prevent the default close behavior

    def mousePressEvent(self, event: QMouseEvent):
        """Close the main_window on any mouse button press."""
        # if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
        #     self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        """Close the main_window on pressing the Escape key."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)  # Pass other key events to the parent

    def setup_window(self):
        """Set up the main main_window properties."""
        self.setWindowTitle(f"{CONFIG.INTERNAL_PROGRAM_NAME} - Main")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def open_special_menu(self):
        if hasattr(self, "special_menu"):
            self.hide()
            show_special_menu(self.special_menu)
        else:
            print("No SpecialMenu here...")

    def event(self, event):
        """Handle the custom filtered_event to show the main_window."""

        if isinstance(event, ShowWindowEvent):
            pie_menu: PieMenu = event.child_window
            if pie_menu is not None:
                print(f"Showing switcher {pie_menu.view.objectName()}")
                # Hide siblings of class PieMenuTaskSwitcher
                for sibling in self.children():
                    if sibling is not pie_menu and isinstance(sibling, PieMenu):
                        sibling.hide()
                pie_menu.show()
                if "Task" in pie_menu.view.objectName():
                    self.refresh()
                self.pie_menu_pos = self.show_pie_window(pie_menu)  # Safely call show_pie_window when the filtered_event is posted
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

    def refresh(self):
        # Start the background task
        threading.Thread(target=self.update_pm_task_buttons, daemon=True).start()

    def show_pie_window(self, pie_menu):
        """Display the main window and bring it to the foreground."""
        try:
            # Get the main window handle
            hwnd = int(self.winId())

            # Get the current mouse position
            cursor_pos = QCursor.pos()

            screen = QGuiApplication.screenAt(cursor_pos)  # Detect screen at cursor position
            screen_geometry = screen.availableGeometry()  # Get the screen geometry

            # Get screen dimensions
            screen_left = screen_geometry.left()
            screen_top = screen_geometry.top()
            screen_right = screen_geometry.right()
            screen_bottom = screen_geometry.bottom()

            # Calculate initial new_x and new_y
            new_x = cursor_pos.x() - (pie_menu.width() // 2)
            new_y = cursor_pos.y() - (pie_menu.height() // 2)

            # Ensure window position stays within screen bounds
            corrected_x = max(screen_left, min(new_x, screen_right - pie_menu.width()))
            corrected_y = max(screen_top, min(new_y, screen_bottom - pie_menu.height()))

            # Normalize top left for other monitors
            corrected_x -= screen_left
            corrected_y -= screen_top

            if pie_menu is not None:
                pie_menu.move(corrected_x, corrected_y)

            # Set geometry for pie_window on the current screen
            self.move(screen_geometry.topLeft())  # Move to the top-left of the screen
            self.setFixedSize(screen_geometry.width(), screen_geometry.height())  # Ensure the window size matches screen size
            self.view.setFixedSize(screen_geometry.width(), screen_geometry.height())  # Ensure view size matches screen size
            self.scene.setSceneRect(0, 0, screen_geometry.width(), screen_geometry.height())

            # Prevents flashing a frame of the last window position when calling show()
            self.setWindowOpacity(0)  # Make the window fully transparent
            self.show()
            QTimer.singleShot(1, lambda: self.setWindowOpacity(1))  # Restore opacity after a short delay

            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)

            return cursor_pos

        except Exception as e:
            print(f"Error showing the main window: {e}")

    def get_pie_menu_and_index(self, button_index: int, pie_menu_type: PieMenuType) -> Tuple[PieMenu, int]:
        """Helper function to calculate the Pie Menu and index dynamically."""
        # Use the Enum to determine which list to use
        pie_menus = {
            PieMenuType.TASK_SWITCHER: self.pie_menus_primary,
            PieMenuType.WIN_CONTROL: self.pie_menus_secondary
        }.get(pie_menu_type)

        if pie_menus is None:
            raise ValueError(f"Invalid pie menu type: {pie_menu_type}.")

        max_buttons = CONFIG.INTERNAL_MAX_BUTTONS

        pie_menu_index = button_index // max_buttons  # Determine the task switcher index
        index = button_index % max_buttons  # Calculate the index within the task switcher

        if pie_menu_index < len(pie_menus):
            pie_menu = pie_menus[pie_menu_index]
        else:
            raise ValueError(f"Invalid button index {index}: exceeds available task switchers.")

        return pie_menu, index

    def setup_window_control_buttons(self):
        actual_self = self
        app_info_cache = load_cache()

        button_config = [
            {"index": (0, 0), "label": "MAXIMIZE",
             "action": lambda: toggle_maximize_window_at_cursor(actual_self),
             "icon": EXTERNAL_ICON_PATHS.get("window_maximize"), "is_inverted": True},
            {"index": (0, 1), "label": "Restore Minimized",
             "action": restore_last_minimized_window,
             "icon": EXTERNAL_ICON_PATHS.get("change"), "is_inverted": True},
            {"index": (0, 2), "label": "Forward!",
             "action": lambda: pyautogui.hotkey('alt', 'right'),
             "icon": EXTERNAL_ICON_PATHS.get("arrow-right"), "is_inverted": True},
            {"index": (0, 3), "label": "Get All Expl. Win.",
             "action": focus_all_explorer_windows,
             "icon": EXTERNAL_ICON_PATHS.get("folders"), "is_inverted": True},
            {"index": (0, 4), "label": "Minimize",
             "action": lambda: minimize_window_at_cursor(actual_self),
             "icon": EXTERNAL_ICON_PATHS.get("window_minimize"), "is_inverted": True},
            {"index": (0, 5), "label": "Center Window",
             "action": lambda: center_window_at_cursor(actual_self),
             "icon": EXTERNAL_ICON_PATHS.get("center"), "is_inverted": True},
            {"index": (0, 6), "label": ""},
            {"index": (0, 7), "label": ""},
            {"index": (1, 0), "label": "Exploreraaaaaaaaaaaaaaaaaaaaaaaaa 🚀",
             "action": lambda: launch_app(app_info_cache.get("explorer.exe", {}).get("exe_path")),
             "icon": app_info_cache.get("explorer.exe", {}).get("icon_path"), "is_inverted": False},
            {"index": (1, 1), "label": "PyCharm 🚀",
             "action": lambda: launch_app(app_info_cache.get("pycharm64.exe", {}).get("exe_path")),
             "icon": app_info_cache.get("pycharm64.exe", {}).get("icon_path"), "is_inverted": False},
            {"index": (1, 2), "label": "Sourcetree 🚀",
             "action": lambda: launch_app(app_info_cache.get("sourcetree.exe", {}).get("exe_path")),
             "icon": app_info_cache.get("sourcetree.exe", {}).get("icon_path"), "is_inverted": False},
            {"index": (1, 3), "label": ""},
            {"index": (1, 4), "label": "Blender 🚀",
             "action": lambda: launch_app(app_info_cache.get("blender.exe", {}).get("exe_path")),
             "icon": app_info_cache.get("blender.exe", {}).get("icon_path"), "is_inverted": False},
            {"index": (1, 5), "label": ""},
            {"index": (1, 6), "label": "Notepad 🚀",
             "action": lambda: launch_app(app_info_cache.get("notepad.exe", {}).get("exe_path")),
             "icon": app_info_cache.get("notepad.exe", {}).get("icon_path"), "is_inverted": False},
            {"index": (1, 7), "label": ""},
        ]

        for config in button_config:
            i, j = config["index"]
            button = self.pie_menus_secondary[i].pie_buttons[j]

            button.set_label_1_text(config.get("label", ""))
            if config["label"]:
                button.setEnabled(True)
            else:
                button.setEnabled(False)

            if "action" in config:
                button.set_left_click_action(lambda c=config: (
                    self.hide(),
                    QTimer.singleShot(0, lambda: c["action"]()),
                ))

            if "icon" and "icon_path" and "is_inverted" in config:
                button.update_icon(config["icon"], is_invert_icon=config["is_inverted"])

    # Button Management
    def update_pm_task_buttons(self):
        """Update main_window buttons with current main_window information."""
        if cache_being_cleared:
            print("DANGER! CACHE IS BEING CLEARED. SKIP.")
            return

        all_open_windows_info_by_hwnd = self.manager.get_window_hwnd_mapping()
        app_info_cache = load_cache()
        final_button_updates = []
        processed_handles = set()

        def create_button_update(button_index, hwnd, title, exe_name, instance):
            cache_entry = app_info_cache.get(exe_name)
            if not cache_entry:
                print(f"Cache entry for {exe_name} not found, skipping window")
                return None

            app_name = cache_entry.get("app_name", "")
            app_icon_path = cache_entry.get("icon_path")
            button_text = f"{title} ({instance})" if instance != 0 else title
            # sends "fixed" for task_type, but it's not used for now so doesn't matter
            return {
                "index": button_index,
                "task_type": "program_window_fixed",
                "properties": {
                    "app_name": app_name,
                    "text_1": button_text,
                    "text_2": app_name,
                    "window_handle": hwnd,
                    "app_icon_path": app_icon_path,
                    "exe_name": exe_name
                }
            }

        def process_fixed_buttons() -> None:
            """Ensure fixed buttons retain their assigned windows or remain empty."""
            fixed_buttons = self.button_info.filter_buttons("task_type", "program_window_fixed")
            fixed_windows = _get_currently_assigned_fixed_windows()
            already_assigned_windows = set(fixed_windows.values())

            for button in fixed_buttons:
                button_index = _get_button_index(button)
                if button_index is None:
                    continue

                exe_name = button["properties"].get("exe_name", "")
                assigned_hwnd = fixed_windows.get(button_index)

                if assigned_hwnd and _is_valid_assigned_window(assigned_hwnd, exe_name):
                    _process_valid_window(button_index, assigned_hwnd, exe_name)
                else:
                    _process_invalid_window(button_index, assigned_hwnd, exe_name, already_assigned_windows)

        def _get_currently_assigned_fixed_windows() -> Dict[int, int]:
            """Returns a dictionary of currently assigned windows to fixed buttons."""
            fixed_windows: Dict[int, int] = {}  # {button_index: hwnd}
            for hwnd, button_index in self.windowHandles_To_buttonIndexes_map.items():
                if button_index in {index for index, btn in self.button_info.items() if btn.get("task_type") == "program_window_fixed"}:
                    fixed_windows[button_index] = hwnd
            return fixed_windows

        def _get_button_index(button: Dict) -> Optional[int]:
            """Returns the index of the given button in self.button_info, or None if not found."""
            return next((index for index, b in self.button_info.items() if b is button), None)

        def _is_valid_assigned_window(assigned_hwnd: int, exe_name: str) -> bool:
            """Checks if the assigned window is still valid (exists and matches the exe_name)."""
            return (
                    assigned_hwnd
                    and assigned_hwnd in all_open_windows_info_by_hwnd
                    and all_open_windows_info_by_hwnd[assigned_hwnd][1] == exe_name
            )

        def _process_valid_window(button_index: int, assigned_hwnd: int, exe_name: str) -> None:
            """Processes a valid assigned window: creates an update and adds the handle to processed handles."""
            title, _, instance = all_open_windows_info_by_hwnd[assigned_hwnd]
            update = create_button_update(button_index, assigned_hwnd, title, exe_name, instance)
            if update:
                final_button_updates.append(update)
                processed_handles.add(assigned_hwnd)

        def _process_invalid_window(button_index: int, assigned_hwnd: Optional[int], exe_name: str,
                                    already_assigned_windows: Set[int]) -> None:
            """Processes an invalid assigned window: removes old mapping, tries to find a new window, or leaves the button empty."""
            if assigned_hwnd:  # Remove potentially invalid mapping
                self.windowHandles_To_buttonIndexes_map.pop(assigned_hwnd, None)

            new_hwnd = _find_new_window(exe_name, already_assigned_windows)

            if new_hwnd:
                _assign_new_window(button_index, new_hwnd, exe_name, already_assigned_windows)
            else:
                _leave_button_empty(button_index, exe_name)

        def _find_new_window(exe_name: str, already_assigned_windows: Set[int]) -> Optional[int]:
            """Finds a new window that matches the given exe_name and is not already processed or assigned."""
            for hwnd, (title, window_exe, instance) in all_open_windows_info_by_hwnd.items():
                if window_exe == exe_name and hwnd not in processed_handles and hwnd not in already_assigned_windows:
                    return hwnd
            return None

        def _assign_new_window(button_index: int, new_hwnd: int, exe_name: str, already_assigned_windows: Set[int]) -> None:
            """Assigns a new window to the button: creates an update, adds the handle to processed handles and assigned windows, and updates the mapping."""
            title, _, instance = all_open_windows_info_by_hwnd[new_hwnd]
            update = create_button_update(button_index, new_hwnd, title, exe_name, instance)
            if update:
                final_button_updates.append(update)
                processed_handles.add(new_hwnd)
                already_assigned_windows.add(new_hwnd)
                self.windowHandles_To_buttonIndexes_map[new_hwnd] = button_index

        def _leave_button_empty(button_index: int, exe_name: str) -> None:
            """Leaves the button empty by creating an update with hwnd=0."""
            update = create_button_update(button_index, 0, "", exe_name, 0)
            if update:
                final_button_updates.append(update)

        def process_existing_mappings(pie_menu_index: int) -> None:
            """Process existing window mappings for non-fixed buttons, leaving fixed ones intact."""
            # Windows that are already assigned and still exist
            previously_assigned_windows: Dict[int, Tuple[str, str, int]] = {
                hwnd: all_open_windows_info_by_hwnd[hwnd]
                for hwnd in self.windowHandles_To_buttonIndexes_map
                if hwnd in all_open_windows_info_by_hwnd
            }

            # for hwnd, (title, exe_name, instance) in previously_assigned_windows.items():
            #     print(f"Window Handle: {hwnd}, Title: {title}, Executable: {exe_name}, Instance: {instance}")

            # Calculate the start and end of the Pie Menu range (8 buttons per menu)
            menu_start = pie_menu_index * 8
            menu_end = menu_start + 8
            menu_slots = set(range(menu_start, menu_end))

            # Pass on non-fixed already-assigned buttons in Pie Menu 1
            for hwnd, mapped_index in list(self.windowHandles_To_buttonIndexes_map.items()):
                if mapped_index in self.fixed_button_indexes:
                    continue  # Skip fixed buttons
                if (hwnd in previously_assigned_windows and
                        hwnd not in processed_handles and
                        hwnd not in self.fixed_windows and
                        mapped_index in menu_slots):
                    title, exe_name, instance = previously_assigned_windows[hwnd]
                    update = create_button_update(mapped_index, hwnd, title, exe_name, instance)
                    if update:
                        final_button_updates.append(update)
                        processed_handles.add(hwnd)

        def fill_empty_buttons(pie_menu_index: int) -> None:
            """Fill any remaining empty buttons in a specific Pie Menu with unprocessed windows, skipping fixed buttons."""
            used_indexes: Set[int] = {update["index"] for update in final_button_updates}
            all_empty_indexes: Set[int] = set(range(pie_menu_index * 8, (pie_menu_index + 1) * 8)) - used_indexes

            for button_index in sorted(all_empty_indexes):
                if button_index in self.fixed_button_indexes:
                    continue  # Skip fixed buttons

                for hwnd, (title, exe_name, instance) in all_open_windows_info_by_hwnd.items():
                    if hwnd not in processed_handles and hwnd not in self.fixed_windows:
                        update = create_button_update(button_index, hwnd, title, exe_name, instance)
                        if update:
                            final_button_updates.append(update)
                            processed_handles.add(hwnd)
                            self.windowHandles_To_buttonIndexes_map[hwnd] = button_index
                            break

        # Execute the process starting with Fixed Buttons
        process_fixed_buttons()

        # Pre-calculate fixed button information
        self.fixed_button_indexes = {
            index for index, btn in self.button_info.items()
            if btn.get("task_type") == "program_window_fixed"
        }

        # Get windows assigned to fixed buttons
        self.fixed_windows = {
            hwnd for hwnd, index in self.windowHandles_To_buttonIndexes_map.items()
            if index in self.fixed_button_indexes
        }

        # Process the rest, one Pie Menu at a time,
        # so already-assigned Windows only jump
        # if there is a free slot in the lower-index Pie Menu
        for pie_menu_index in range(CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY):
            process_existing_mappings(pie_menu_index)
            fill_empty_buttons(pie_menu_index)

        # print(self.windowHandles_To_buttonIndexes_map)
        # print("\n")

        # for update in final_button_updates:
        #     print(update)

        self.clean_up_stale_window_mappings(final_button_updates)

        # Emit updates
        for pie_menu in self.pie_menus_primary:
            pie_menu.update_buttons_signal.emit(final_button_updates)
        for pie_menu in self.pie_menus_secondary:
            pie_menu.update_buttons_signal.emit(final_button_updates)

    def clean_up_stale_window_mappings(self, final_button_updates):
        # Clean up stale window mappings
        if len(self.windowHandles_To_buttonIndexes_map) > 40:
            valid_handles = {update["properties"]["window_handle"] for update in final_button_updates}
            self.windowHandles_To_buttonIndexes_map = {
                handle: button_id
                for handle, button_id in self.windowHandles_To_buttonIndexes_map.items()
                if handle in valid_handles
            }