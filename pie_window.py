import threading
from threading import Lock
from typing import Dict, List

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QMouseEvent, QKeyEvent, QCursor
from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsView, QApplication, QWidget

from config import CONFIG
from events import ShowWindowEvent, HotkeyReleaseEvent
from pie_button import PieButton
from pie_menu_task_switcher import PieMenuTaskSwitcher
from special_menu import SpecialMenu
from window_functions import show_pie_window, get_filtered_list_of_windows, focus_window_by_handle, \
    close_window_by_handle, load_cache, show_special_menu
from window_manager import WindowManager

manager = WindowManager.get_instance()


class PieWindow(QMainWindow):
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

        self.num_pie_menus = 2
        self.button_mapping_lock = Lock()
        self.last_window_handles = []
        self.pie_button_texts = ["Empty" for _ in range(CONFIG.MAX_BUTTONS * self.num_pie_menus)]
        self.windowHandles_To_buttonIndexes_map = {}

        self.active_child = 1
        self.is_window_open = False

        # Create PieMenuTaskSwitcher with this main_window as parent
        self.pm_task_switcher = PieMenuTaskSwitcher(obj_name="PieMenuTaskSwitcher", parent=self)
        self.pm_task_switcher_2 = PieMenuTaskSwitcher(obj_name="PieMenuTaskSwitcher_2", parent=self)
        self.pm_task_switcher_2.hide()

        self.special_menu = SpecialMenu(obj_name="SpecialMenu",parent=None)
        self.special_menu.hide()

        # Start auto-refreshing every REFRESH_INTERVAL milliseconds
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        self.auto_refresh_timer.start(CONFIG.REFRESH_INTERVAL)  # Periodic refresh

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
        self.setWindowTitle("Main Window with Graphics View and Task Switcher Pie")
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
            task_switcher: PieMenuTaskSwitcher = event.child_window
            if task_switcher is not None:
                print(f"Showing switcher {task_switcher.view.objectName()}")
                # Hide siblings of class PieMenuTaskSwitcher
                for sibling in self.children():
                    if sibling is not task_switcher and isinstance(sibling, PieMenuTaskSwitcher):
                        sibling.hide()
                task_switcher.show()
                self.refresh()
                show_pie_window(event.window, task_switcher)  # Safely call show_pie_window when the filtered_event is posted
            return True
        elif isinstance(event, HotkeyReleaseEvent):
            task_switcher = event.child_window
            pie_buttons: Dict[int, PieButton]  # Where 'SomeType' is the type of items in pie_buttons

            # If there's an active section, click that button
            if hasattr(task_switcher.area_button, 'current_active_section'):
                active_section = task_switcher.area_button.current_active_section
                if active_section != -1:
                    task_switcher.pie_buttons[active_section].trigger_left_click_action()
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
        print("Refreshing!")
        self.update_buttons()

    # Button Management
    def update_buttons(self):
        """Update main_window buttons with current main_window information."""

        def background_task():
            window_mapping = get_filtered_list_of_windows(self)
            temp_button_texts = self.pie_button_texts.copy()
            app_name_cache = load_cache()
            final_button_updates = []

            def get_free_button_indexes():
                """Returns available button indexes, excluding fixed slots."""
                return [
                    j for j in range(CONFIG.MAX_BUTTONS * self.num_pie_menus)
                    if j not in CONFIG.FIXED_PIE_SLOTS.values()
                       and temp_button_texts[j] == "Empty"
                ]

            # Process each window
            for window_handle, (window_title, exe_name, instance_number) in window_mapping.items():
                # Get app information from cache
                cache_entry = app_name_cache.get(exe_name, {})
                app_name = cache_entry.get("app_name")
                app_icon_path = cache_entry.get("icon_path")

                # Format button text
                button_text = (f"{window_title} ({instance_number})"
                               if instance_number != 0 else window_title)

                # Get or assign button index
                button_index = self.windowHandles_To_buttonIndexes_map.get(window_handle)

                # Handle fixed slots
                if app_name in CONFIG.FIXED_PIE_SLOTS:
                    button_index = CONFIG.FIXED_PIE_SLOTS[app_name]
                    self.windowHandles_To_buttonIndexes_map[window_handle] = button_index
                else:
                    # Find free button if needed
                    free_indexes = get_free_button_indexes()
                    if not free_indexes:
                        continue

                    if button_index is None or (button_index > 7
                                                and button_index > min(free_indexes)):
                        button_index = free_indexes[0]
                        self.windowHandles_To_buttonIndexes_map[window_handle] = button_index

                # Update button text and collect updates
                temp_button_texts[button_index] = button_text
                final_button_updates.append({
                    "index": button_index,
                    "text_1": button_text,
                    "text_2": app_name,
                    "window_handle": window_handle,
                    "app_icon_path": app_icon_path
                })

            # Clean up stale window mappings
            if len(self.windowHandles_To_buttonIndexes_map) > 20:
                valid_handles = {update["window_handle"] for update in final_button_updates}
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

        for update in button_updates:
            button_index = update["index"]
            button_text_1 = update["text_1"]
            button_text_2 = update["text_2"]
            window_handle = update["window_handle"]
            app_icon_path = update["app_icon_path"]
            # Above the size of one pie menu, go to the next
            if button_index > CONFIG.MAX_BUTTONS - 1:
                button_index = button_index % 8
                task_switcher = self.pm_task_switcher_2
            else:
                task_switcher = self.pm_task_switcher

            self.pie_button_texts[button_index] = button_text_1

            task_switcher: QWidget
            task_switcher.pie_buttons: List[PieButton]
            task_switcher.pie_buttons[button_index].set_label_1_text(button_text_1)
            task_switcher.pie_buttons[button_index].set_label_2_text(button_text_2)
            task_switcher.pie_buttons[button_index].update_icon(app_icon_path)

            # Disconnect any previous connections first
            try:
                task_switcher.pie_buttons[button_index].clicked.disconnect()
            except TypeError:
                pass  # No connections to disconnect

            # Set the clicking actions
            task_switcher.pie_buttons[button_index].set_left_click_action(
                lambda hwnd=window_handle: (
                    # QTimer.singleShot(100, lambda: focus_window_by_handle(hwnd)),  # Delay in event loop
                    self.hide(),
                    QTimer.singleShot(0, lambda: focus_window_by_handle(hwnd)),
                )
            )
            task_switcher.pie_buttons[button_index].set_middle_click_action(
                lambda hwnd=window_handle: (
                    QTimer.singleShot(0, lambda: close_window_by_handle(hwnd)),
                    self.refresh(),
                )
            )
            task_switcher.pie_buttons[button_index].setEnabled(True)

        # Clear button attributes when button index not among updates
        for i in range(CONFIG.MAX_BUTTONS * self.num_pie_menus):
            if i not in [update["index"] for update in button_updates]:
                index = i
                self.pie_button_texts[i] = "Empty"
                # Above the size of one pie menu, go to the next
                if i > CONFIG.MAX_BUTTONS - 1:
                    index = i % 8
                    task_switcher = self.pm_task_switcher_2
                else:
                    task_switcher = self.pm_task_switcher
                try:
                    task_switcher.pie_buttons[index].set_left_click_action(action=None)
                    task_switcher.pie_buttons[index].set_right_click_action(action=None)
                    task_switcher.pie_buttons[index].set_middle_click_action(action=None)

                except TypeError:
                    pass
                # self.pie_buttons[i].clicked.connect(
                #     lambda checked: (
                #         self.parent().hide(),
                #     )
                # )
                task_switcher.pie_buttons[index].setEnabled(False)  # Disable the button
                task_switcher.pie_buttons[index].set_label_1_text("Empty")
                task_switcher.pie_buttons[index].set_label_2_text("")
                task_switcher.pie_buttons[index].update_icon("")
