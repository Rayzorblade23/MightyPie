import threading
from threading import Lock

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QMouseEvent, QKeyEvent, QCursor
from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsView, QApplication

from config import CONFIG
from events import ShowWindowEvent, HotkeyReleaseEvent
from pie_menu_task_switcher import PieMenuTaskSwitcher
from window_controls import create_window_controls
from window_functions import show_pie_window, get_filtered_list_of_window_titles, get_application_info, focus_window_by_handle
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

        self.button_mapping_lock = Lock()
        self.last_window_titles = []
        self.pie_button_texts = ["Empty" for _ in range(CONFIG.MAX_BUTTONS * 2)]
        self.buttons_To_windows_map = {}

        self.active_child = 1
        self.is_window_open = False

        # Create PieMenuTaskSwitcher with this main_window as parent
        self.pm_task_switcher = PieMenuTaskSwitcher(obj_name="PieMenuTaskSwitcher", parent=self)
        self.pm_task_switcher_2 = PieMenuTaskSwitcher(obj_name="PieMenuTaskSwitcher_2", parent=self)
        self.pm_task_switcher_2.hide()

        # Create main_window control buttons with fixed sizes and actions
        button_widget, minimize_button, close_button = create_window_controls(main_window=self)

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

            # If there's an active section, click that button
            if hasattr(task_switcher.area_button, 'current_active_section'):
                active_section = task_switcher.area_button.current_active_section
                if active_section != -1:
                    task_switcher.pie_buttons[active_section].click()
            self.hide()
            return True
        return super().event(event)

    def auto_refresh(self):
        """Automatically monitor and refresh windows periodically in a thread-safe way."""
        # start_time = time.time()

        # Lock access to shared data to ensure thread safety
        with self.button_mapping_lock:
            current_window_titles = get_filtered_list_of_window_titles(self)
            # only actually refresh when windows have opened or closed
            if current_window_titles != self.last_window_titles:
                self.last_window_titles = current_window_titles
                self.refresh()  # Safely call the refresh method to update UI

        # elapsed_time = time.time() - start_time
        # print(f"auto_refresh took {elapsed_time:.3f} seconds")

    def refresh(self):
        print("Refreshing!")
        self.update_buttons()

    # Button Management
    def update_buttons(self):
        """Update main_window buttons with current main_window information."""

        def get_free_button_index(temp_pie_button_names, button_text = ""):
            """Find a free button index in the button names list."""
            for j in range(CONFIG.MAX_BUTTONS * 2):
                if temp_pie_button_names[j] == "Empty" or temp_pie_button_names[j] == button_text:
                    return j
            return None

        def background_task():
            windows_titles = get_filtered_list_of_window_titles(self)

            final_button_updates = []

            temp_pie_button_texts = (
                self.pie_button_texts
            )  # because the names need to be evaluated here

            for i, window_title in enumerate(windows_titles):
                window_handle = manager.get_window_titles_to_hwnds_map().get(window_title)
                if not window_handle:  # Exclude windows with no handle
                    continue

                result = get_application_info(window_handle)

                # Check if the result is a tuple (app_name, app_icon_path)
                if isinstance(result, tuple):
                    app_name, app_icon_path = result
                elif isinstance(result, str):
                    # If result is a string, print the error and handle it
                    print(f"Error: {result}")
                    app_name, app_icon_path = None, None  # Default values or handle the error case
                else:
                    # Handle unexpected result type
                    print(f"Unexpected result: {result}")
                    app_name, app_icon_path = None, None  # Default values or handle the error case

                button_title = (
                    window_title
                    if f" - {app_name}" not in window_title
                    else window_title.replace(f" - {app_name}", "")
                )
                button_text_1 = button_title
                button_text_2 = app_name

                # Check if the main_window is already assigned a button
                button_index = self.buttons_To_windows_map.get(window_handle)

                # If Button Index not assigned, find a free button
                if button_index is None or button_index > 7:
                    button_index = get_free_button_index(temp_pie_button_texts, button_text_1)
                    # If Button Index still not assigned, no free button for you :(
                    if button_index is None:
                        continue
                    # Assign Button Index to the main_window handle
                    self.buttons_To_windows_map[window_handle] = button_index

                temp_pie_button_texts[button_index] = button_text_1  # Update button name


                final_button_updates.append(
                    {
                        "index": button_index,
                        "text_1": button_text_1,
                        "text_2": button_text_2,
                        "window_handle": window_handle,
                        "app_icon_path": app_icon_path
                    }
                )

            # Clean buttons_To_windows_map dict of old windows
            if len(self.buttons_To_windows_map) > 20:
                # Step 1: Extract valid window_titles_To_hwnds_map from button_updates
                valid_window_handles = {
                    update["window_handle"] for update in final_button_updates
                }

                # Step 2: Filter buttons_To_windows_map to only keep pairs where the window_handle is in valid_window_handles
                self.buttons_To_windows_map = {
                    handle: button_id
                    for handle, button_id in self.buttons_To_windows_map.items()
                    if handle in valid_window_handles
                }
            # Emit the signal instead of using invokeMethod
            self.update_buttons_signal.emit(final_button_updates)

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

            task_switcher.pie_buttons[button_index].set_label_1_text(button_text_1)
            task_switcher.pie_buttons[button_index].set_label_2_text(button_text_2)
            task_switcher.pie_buttons[button_index].update_icon(app_icon_path)

            # Disconnect any previous connections first
            try:
                task_switcher.pie_buttons[button_index].clicked.disconnect()
            except TypeError:
                pass  # No connections to disconnect

            # Connect new signal
            task_switcher.pie_buttons[button_index].clicked.connect(
                lambda checked, hwnd=window_handle: (
                    # QTimer.singleShot(100, lambda: focus_window_by_handle(hwnd)),  # Delay in event loop
                    self.hide(),
                    QTimer.singleShot(0, lambda: focus_window_by_handle(hwnd)),
                )
            )
            task_switcher.pie_buttons[button_index].setEnabled(True)

        # Clear button attributes when button index not among updates
        for i in range(CONFIG.MAX_BUTTONS * 2):
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
                    task_switcher.pie_buttons[index].clicked.disconnect()

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
