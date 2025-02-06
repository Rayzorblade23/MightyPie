import os
import os
import subprocess
import sys
import threading
import time
from threading import Lock
from typing import Dict, List, Tuple

import psutil
import pyautogui
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QPoint, QCoreApplication
from PyQt6.QtGui import QMouseEvent, QKeyEvent, QCursor
from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsView, QApplication

from GUI.pie_button import PieButton
from button_info import ButtonInfo
from config import CONFIG
from events import ShowWindowEvent, HotkeyReleaseEvent
from functions.icon_functions_and_paths import EXTERNAL_ICON_PATHS
from functions.window_functions import show_pie_window, get_filtered_list_of_windows, focus_window_by_handle, \
    close_window_by_handle, load_cache, show_special_menu, toggle_maximize_window_at_cursor, minimize_window_at_cursor, launch_app, \
    cache_being_cleared, restore_last_minimized_window
from pie_menu import PieMenu
from special_menu import SpecialMenu
from window_manager import WindowManager

manager = WindowManager.get_instance()


class PieWindow(QMainWindow):
    EXIT_CODE_REBOOT = 122

    # Add a custom signal for thread-safe updates
    update_buttons_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        # Connect the custom signal to the update method
        self.update_buttons_signal.connect(self.update_button_ui)

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

        self.pie_menu_pos = QPoint()
        self.button_mapping_lock = Lock()
        self.last_window_handles = []
        self.pie_button_texts = ["Empty" for _ in range(CONFIG._MAX_BUTTONS * CONFIG._NUM_PIE_TASK_SWITCHERS)]
        self.windowHandles_To_buttonIndexes_map = {}

        self.active_child = 1
        self.is_window_open = False

        # Create Pie Menus with this main_window as parent
        self.pm_task_switchers: list[PieMenu] = []  # List to hold the task switchers
        for i in range(1, CONFIG._NUM_PIE_TASK_SWITCHERS + 1):  # Adjust the range if the number of task switchers changes
            task_switcher = PieMenu(obj_name=f"PieMenuTaskSwitcher_{i}", parent=self)
            if i > 1:  # Hide task switchers 2 and 3 initially
                task_switcher.hide()
            self.pm_task_switchers.append(task_switcher)

        self.pm_win_control = PieMenu(obj_name="PieMenuWindowControl", parent=self)
        self.pm_win_control.hide()
        self.setup_window_control_buttons()

        # For now, right-click should always just hide
        for i in range(CONFIG._MAX_BUTTONS * CONFIG._NUM_PIE_TASK_SWITCHERS):
            task_switcher, index = self.get_task_switcher_and_index(i)
            task_switcher.pie_buttons[index].set_right_click_action(action=lambda: self.hide())

        for i in range(CONFIG._MAX_BUTTONS):
            self.pm_win_control.pie_buttons[i].set_right_click_action(action=lambda: self.hide())

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
        self.setWindowTitle(f"{CONFIG._PROGRAM_NAME} - Main")
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
                self.pie_menu_pos = show_pie_window(event.window, pie_menu)  # Safely call show_pie_window when the filtered_event is posted
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
        self.update_pm_task_buttons()

    def get_task_switcher_and_index(self, button_index: int) -> Tuple[PieMenu, int]:
        """Helper function to calculate the task switcher and index dynamically."""
        task_switchers = self.pm_task_switchers  # Assuming this is a list of task switchers
        max_buttons = CONFIG._MAX_BUTTONS

        task_switcher_index = button_index // max_buttons  # Determine the task switcher index
        index = button_index % max_buttons  # Calculate the index within the task switcher

        if task_switcher_index < len(task_switchers):
            task_switcher = task_switchers[task_switcher_index]
        else:
            raise ValueError(f"Invalid button index {index}: exceeds available task switchers.")

        return task_switcher, index

    def setup_window_control_buttons(self):
        actual_self = self
        self.pm_win_control.pie_buttons: List[PieButton]

        self.pm_win_control.pie_buttons[0].set_label_1_text("MAXIMIZE")
        self.pm_win_control.pie_buttons[0].set_left_click_action(lambda: (
            self.hide(),
            QTimer.singleShot(0, lambda: toggle_maximize_window_at_cursor(actual_self)),
        ))
        self.pm_win_control.pie_buttons[0].update_icon(EXTERNAL_ICON_PATHS.get("window_maximize"), is_invert_icon=True)

        self.pm_win_control.pie_buttons[1].set_label_1_text("Restore Minimized")
        self.pm_win_control.pie_buttons[1].set_left_click_action(lambda: (
            self.hide(),
            QTimer.singleShot(0, lambda: restore_last_minimized_window()),
        ))
        self.pm_win_control.pie_buttons[1].update_icon(EXTERNAL_ICON_PATHS.get("change"), is_invert_icon=True)

        self.pm_win_control.pie_buttons[2].set_label_1_text("Forward!")
        self.pm_win_control.pie_buttons[2].set_left_click_action(lambda: (
            self.hide(),
            QTimer.singleShot(0, lambda: pyautogui.hotkey('alt', 'right')),
        ))
        self.pm_win_control.pie_buttons[2].setEnabled(True)  # Disable the button
        self.pm_win_control.pie_buttons[2].update_icon(EXTERNAL_ICON_PATHS.get("arrow-right"), is_invert_icon=True)

        self.pm_win_control.pie_buttons[3].set_label_1_text("")
        self.pm_win_control.pie_buttons[3].setEnabled(False)  # Disable the button

        self.pm_win_control.pie_buttons[4].set_label_1_text("Minimize")
        self.pm_win_control.pie_buttons[4].set_left_click_action(lambda: (
            self.hide(),
            QTimer.singleShot(0, lambda: minimize_window_at_cursor(actual_self)),
        ))
        self.pm_win_control.pie_buttons[4].update_icon(EXTERNAL_ICON_PATHS.get("window_minimize"), is_invert_icon=True)

        self.pm_win_control.pie_buttons[5].set_label_1_text("")
        self.pm_win_control.pie_buttons[5].setEnabled(False)  # Disable the button

        self.pm_win_control.pie_buttons[6].set_label_1_text("")
        self.pm_win_control.pie_buttons[6].setEnabled(False)  # Disable the button

        self.pm_win_control.pie_buttons[7].set_label_1_text("")
        self.pm_win_control.pie_buttons[7].setEnabled(False)  # Disable the button

    # Button Management
    def update_pm_task_buttons(self):
        """Update main_window buttons with current main_window information."""

        def background_task():
            if cache_being_cleared:
                print("DANGER! CACHE IS BEING CLEARED. SKIP.")
                return

            button_info = ButtonInfo()
            window_mapping = manager.get_window_hwnd_mapping()
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
                # sends "fixed" for task_type but it's not used for now so doesn't matter
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

            def process_fixed_buttons():
                """Process all buttons with task_type 'program_window_fixed'"""
                fixed_buttons = button_info.filter_buttons("task_type", "program_window_fixed")

                for button in fixed_buttons:
                    button_index = next(
                        (index for index, b in button_info.items() if b is button), None
                    )
                    if button_index is None:
                        continue

                    exe_name = button["properties"].get("exe_name", "")

                    # Check if there's already a correct window in this slot
                    existing_window = None
                    for hwnd, mapped_index in self.windowHandles_To_buttonIndexes_map.items():
                        if (mapped_index == button_index and
                                hwnd in window_mapping and
                                window_mapping[hwnd][1] == exe_name):
                            existing_window = (hwnd, window_mapping[hwnd])
                            processed_handles.add(hwnd)
                            break

                    if existing_window:
                        # Keep the existing window in place
                        hwnd, (title, _, instance) = existing_window
                        update = create_button_update(button_index, hwnd, title, exe_name, instance)
                        if update:
                            final_button_updates.append(update)
                    else:
                        # Clear any wrong program from this slot
                        final_button_updates[:] = [update for update in final_button_updates
                                                   if update["index"] != button_index]

                        # Remove the window handle mapping for any wrong window at this index
                        for hwnd, mapped_index in list(self.windowHandles_To_buttonIndexes_map.items()):
                            if mapped_index == button_index:
                                del self.windowHandles_To_buttonIndexes_map[hwnd]

                        # Look for a new window of the correct type
                        window_found = False
                        for hwnd, (title, window_exe, instance) in window_mapping.items():
                            if window_exe == exe_name and hwnd not in processed_handles:
                                processed_handles.add(hwnd)
                                window_found = True
                                update = create_button_update(button_index, hwnd, title, exe_name, instance)
                                if update:
                                    final_button_updates.append(update)
                                    self.windowHandles_To_buttonIndexes_map[hwnd] = button_index
                                break

                        if not window_found:
                            # No window found - create empty fixed slot
                            update = create_button_update(button_index, 0, "", exe_name, 0)
                            if update:
                                final_button_updates.append(update)

            def get_valid_windows():
                """Return dict of all currently valid window handles and their info"""
                return {
                    hwnd: window_mapping[hwnd]
                    for hwnd in self.windowHandles_To_buttonIndexes_map
                    if hwnd in window_mapping
                }

            def process_existing_mappings():
                """Process existing window mappings, maintaining positions where possible"""
                valid_windows = get_valid_windows()
                menu_1_slots = set(range(CONFIG._MAX_BUTTONS))

                # First, maintain positions for Menu 1
                for hwnd, mapped_index in list(self.windowHandles_To_buttonIndexes_map.items()):
                    if (hwnd in valid_windows and
                            hwnd not in processed_handles and
                            mapped_index in menu_1_slots):

                        title, exe_name, instance = valid_windows[hwnd]
                        update = create_button_update(mapped_index, hwnd, title, exe_name, instance)
                        if update:
                            final_button_updates.append(update)
                            processed_handles.add(hwnd)

                # Then process Menu 2 windows
                for hwnd, mapped_index in list(self.windowHandles_To_buttonIndexes_map.items()):
                    if (hwnd in valid_windows and
                            hwnd not in processed_handles and
                            mapped_index >= CONFIG._MAX_BUTTONS):

                        # Check if there's space in Menu 1
                        used_indexes = {update["index"] for update in final_button_updates}
                        empty_menu_1_slots = menu_1_slots - used_indexes

                        if empty_menu_1_slots:
                            # Move to Menu 1
                            new_index = min(empty_menu_1_slots)
                            title, exe_name, instance = valid_windows[hwnd]
                            update = create_button_update(new_index, hwnd, title, exe_name, instance)
                            if update:
                                final_button_updates.append(update)
                                processed_handles.add(hwnd)
                                self.windowHandles_To_buttonIndexes_map[hwnd] = new_index
                        else:
                            # Keep in Menu 2
                            title, exe_name, instance = valid_windows[hwnd]
                            update = create_button_update(mapped_index, hwnd, title, exe_name, instance)
                            if update:
                                final_button_updates.append(update)
                                processed_handles.add(hwnd)

            def fill_empty_buttons():
                """Fill any remaining empty buttons with unprocessed windows"""
                used_indexes = {update["index"] for update in final_button_updates}
                all_empty_indexes = set(range(CONFIG._MAX_BUTTONS * CONFIG._NUM_PIE_TASK_SWITCHERS)) - used_indexes

                # Fill remaining empty slots with new windows
                for button_index in sorted(all_empty_indexes):
                    for hwnd, (title, exe_name, instance) in window_mapping.items():
                        if hwnd not in processed_handles:
                            update = create_button_update(button_index, hwnd, title, exe_name, instance)
                            if update:
                                final_button_updates.append(update)
                                processed_handles.add(hwnd)
                                self.windowHandles_To_buttonIndexes_map[hwnd] = button_index
                                break

            # Execute the process
            process_fixed_buttons()
            process_existing_mappings()
            fill_empty_buttons()
            # print(self.windowHandles_To_buttonIndexes_map)
            # print("\n")

            # Clean up stale window mappings
            if len(self.windowHandles_To_buttonIndexes_map) > 40:
                valid_handles = {update["properties"]["window_handle"] for update in final_button_updates}
                self.windowHandles_To_buttonIndexes_map = {
                    handle: button_id
                    for handle, button_id in self.windowHandles_To_buttonIndexes_map.items()
                    if handle in valid_handles
                }

            # Emit updates
            self.update_buttons_signal.emit(final_button_updates)

        # Start the background task
        threading.Thread(target=background_task, daemon=True).start()

    @pyqtSlot(list)
    def update_button_ui(self, button_updates):
        """Update button UI in the main thread."""
        app_info_cache = load_cache()

        for update in button_updates:
            # Extract 'index' directly from the update (not from 'properties')
            button_index = update["index"]

            # Extract the rest of the button info from 'properties'
            button_text_1 = update["properties"]["text_1"]
            button_text_2 = update["properties"]["text_2"]
            window_handle = update["properties"]["window_handle"]
            app_icon_path = update["properties"]["app_icon_path"]
            exe_name = update["properties"]["exe_name"]

            # Determine task switcher and index using the helper function
            task_switcher, index = self.get_task_switcher_and_index(button_index)

            # Update button text and icon
            self.pie_button_texts[index] = button_text_1
            task_switcher.pie_buttons[index].set_label_1_text(button_text_1)
            task_switcher.pie_buttons[index].set_label_2_text(button_text_2)
            task_switcher.pie_buttons[index].update_icon(app_icon_path)

            # Disconnect any previous connections first
            try:
                task_switcher.pie_buttons[index].clicked.disconnect()
            except TypeError:
                pass  # No connections to disconnect

            # Set action for empty reserved buttons
            if window_handle == 0:
                exe_path = app_info_cache.get(exe_name, {}).get("exe_path")
                if exe_path:
                    task_switcher.pie_buttons[index].set_left_click_action(
                        lambda captured_exe_path=exe_path: (
                            self.hide(),
                            QTimer.singleShot(0, lambda: launch_app(captured_exe_path)),
                        )
                    )
                continue

            # Set the clicking actions for windows
            task_switcher.pie_buttons[index].set_left_click_action(
                lambda hwnd=window_handle: (
                    self.hide(),
                    QTimer.singleShot(0, lambda: focus_window_by_handle(hwnd)),
                )
            )
            task_switcher.pie_buttons[index].set_middle_click_action(
                lambda hwnd=window_handle: (
                    QTimer.singleShot(0, lambda: close_window_by_handle(hwnd)),
                    self.refresh(),
                )
            )
            task_switcher.pie_buttons[index].setEnabled(True)

        # Clear button attributes when button index not among updates
        for i in range(CONFIG._MAX_BUTTONS * CONFIG._NUM_PIE_TASK_SWITCHERS):
            if i not in [update["index"] for update in button_updates]:
                task_switcher, index = self.get_task_switcher_and_index(i)

                # Disable the button
                self.pie_button_texts[index] = "Empty"
                task_switcher.pie_buttons[index].set_left_click_action(action=None)
                # task_switcher.pie_buttons[index].set_right_click_action(action=None)
                task_switcher.pie_buttons[index].set_middle_click_action(action=None)
                task_switcher.pie_buttons[index].setEnabled(False)  # Disable the button

                task_switcher.pie_buttons[index].set_label_1_text("Empty")
                task_switcher.pie_buttons[index].set_label_2_text("")
                task_switcher.pie_buttons[index].update_icon("")
