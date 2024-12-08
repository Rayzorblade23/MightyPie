import json
import math
import os
import sys
import ctypes
import time
import psutil
import win32gui
import win32con
import win32process
import win32api
import threading
from threading import Lock
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsEllipseItem,
    QPushButton,
    QHBoxLayout,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QMainWindow,
)
from PyQt6.QtCore import Qt, QRectF, QTimer, QEvent, QSize, Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QBrush,
    QPen,
    QPainter,
    QMouseEvent,
    QKeyEvent,
    QCursor,
    QGuiApplication,
)
import keyboard
from window_controls import create_window_controls
from config import CONFIG

# Global Variables and Initialization
window_handles = {}


# Custom event type for showing the window
class ShowWindowEvent(QEvent):
    def __init__(self, window: QWidget):
        super().__init__(QEvent.Type(1000))  # Custom event type

        self.window = window


class PieTaskSwitcherWindow(QWidget):
    # Add a custom signal for thread-safe updates
    update_buttons_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        # Initialize these attributes BEFORE calling setup methods
        self.button_window_mapping = {}
        self.button_mapping_lock = Lock()
        self.pie_button_texts = ["Empty" for _ in range(CONFIG.MAX_BUTTONS)]
        self.pie_buttons = []
        self.last_window_list = []

        # Connect the custom signal to the update method
        self.update_buttons_signal.connect(self.update_button_ui)

        self.setup_window()  # Configure window properties
        # Create scene and graphical elements
        self.setup_scene_and_view()
        # Create all buttons (task and window controls)
        self.setup_buttons()

        # Start auto-refreshing every REFRESH_INTERVAL milliseconds
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        self.auto_refresh_timer.start(CONFIG.REFRESH_INTERVAL)  # Periodic refresh

    def mousePressEvent(self, event: QMouseEvent):
        """Close the window on any mouse button press."""
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        """Close the window on pressing the Escape key."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)  # Pass other key events to the parent

    def auto_refresh(self):
        """Automatically monitor and refresh windows periodically in a thread-safe way."""
        start_time = time.time()

        # Lock access to shared data to ensure thread safety
        with self.button_mapping_lock:
            current_window_list = get_window_list()
            # only actually refresh when windows have opened or closed
            if current_window_list != self.last_window_list:
                self.last_window_list = current_window_list
                self.refresh()  # Safely call the refresh method to update UI

        elapsed_time = time.time() - start_time
        print(f"auto_refresh took {elapsed_time:.3f} seconds")

    def refresh(self):
        print("Refreshing!")
        self.update_buttons()

    def setup_window(self):
        """Set up the main window properties."""
        self.setWindowTitle("PieTaskSwitcher")
        # Non-resizable window
        self.setFixedSize(*CONFIG.CANVAS_SIZE)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def setup_scene_and_view(self):
        """Set up the scene and graphical elements."""
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setGeometry(0, 0, self.width(), self.height())

        class SmoothCircle(QGraphicsEllipseItem):

            def paint(self, painter: QPainter, option, widget=None):
                # Ensure antialiasing
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setBrush(self.brush())
                painter.setPen(self.pen())
                painter.drawEllipse(self.rect())

        # Use the subclass instead of QGraphicsEllipseItem
        self.inner_circle_main = SmoothCircle(
            QRectF(
                *CONFIG.CANVAS_SIZE, CONFIG.INNER_RADIUS * 2, CONFIG.INNER_RADIUS * 2
            )
        )
        self.inner_circle_main.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.inner_circle_main.setPen(QPen(QColor(30, 30, 30), 7))
        self.scene.addItem(self.inner_circle_main)

        # Create another circle for the outline (slightly thicker)
        self.outline_circle = SmoothCircle(
            QRectF(
                *CONFIG.CANVAS_SIZE, CONFIG.INNER_RADIUS * 2, CONFIG.INNER_RADIUS * 2
            )
        )
        self.outline_circle.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.outline_circle.setPen(QPen(QColor(50, 50, 50), 9))

        # Add the circles to the scene
        self.scene.addItem(self.outline_circle)
        self.scene.addItem(self.inner_circle_main)

        # Ensure the inner circle is on top by setting its Z-index higher than the outline circle
        self.inner_circle_main.setZValue(1)  # Higher Z-value to be in front
        self.outline_circle.setZValue(0)  # Lower Z-value to be behind

    def closeEvent(self, event):
        """Hide the window instead of closing it."""
        self.hide()
        event.ignore()  # Prevent the default close behavior

    def setup_buttons(self):
        """Create and position all buttons."""

        def create_button(
            label,
            object_name,
            action=None,
            fixed_size=True,
            size=(CONFIG.BUTTON_WIDTH, CONFIG.BUTTON_HEIGHT),
            pos=(0, 0),
        ):
            """Creates a QPushButton with optional size, action, and position."""

            button = QPushButton(label, self)
            if fixed_size:
                # Use fixed size if requested or fallback to default size
                button.setFixedSize(QSize(size[0], size[1]))
            else:
                # If no fixed size, button will size to its content
                button.setSizePolicy(
                    QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
                )

            button.setObjectName(object_name)

            # Set the button action if provided
            if action:
                button.clicked.connect(action)

            # Set position if provided
            x, y = pos
            # Set position using `move()`, not `setGeometry()`
            button.move(x, y)

            return button

        # # Create and configure the refresh button
        # self.refresh_button = create_button(
        #     label="R",
        #     object_name="refreshButton",
        #     action=self.refresh,
        #     fixed_size=True,
        #     # Using size instead of geometry
        #     size=(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT),
        #     pos=(
        #         (self.width() - CONFIG.BUTTON_HEIGHT) // 2,
        #         (self.height() - CONFIG.BUTTON_HEIGHT) // 2,
        #     ),  # Using position for x and y
        # )

        # Button Configuration
        # Starting angle
        angle_in_degrees = 0  # Start at 0 degrees

        # Create 8 buttons in a circular pattern, starting with top middle
        for i, name in enumerate(self.pie_button_texts):
            angle_in_degrees = (
                i / 8 * 360
            )  # Calculate button's position using angle_in_radians

            # the base offset here moves the anchor point from top left to center
            offset_x = -CONFIG.BUTTON_WIDTH / 2
            offset_y = CONFIG.BUTTON_HEIGHT / 2

            # the standard anchor position is the middle of a square area at the side of the button
            # the top and bottom buttons don't need it, they should remain centered
            nudge_x = CONFIG.BUTTON_WIDTH / 2 - CONFIG.BUTTON_HEIGHT / 2
            # some buttons need to be nudged so the distribution looks more circular
            # so we nudge the buttons at 45 degrees closer to the x-axis
            nudge_y = CONFIG.BUTTON_HEIGHT / 2

            if i == 1:  # 45 degrees
                offset_x += nudge_x
                offset_y += -nudge_y
            elif i == 2:  # 90 degrees
                offset_x += nudge_x
                offset_y += 0
            elif i == 3:  # 135 degrees
                offset_x += nudge_x
                offset_y += nudge_y
            elif i == 5:  # 225 degrees
                offset_x += -nudge_x
                offset_y += nudge_y
            elif i == 6:  # 270 degrees
                offset_x += -nudge_x
                offset_y += 0
            elif i == 7:  # 315 degrees
                offset_x += -nudge_x
                offset_y += -nudge_y
            else:
                pass

            # distribute the buttons in a circle
            button_pos_x = int(
                CONFIG.CANVAS_SIZE[0] / 2
                + offset_x
                + CONFIG.RADIUS * math.sin(math.radians(angle_in_degrees))
            )
            button_pos_y = int(
                CONFIG.CANVAS_SIZE[1] / 2
                - offset_y
                - CONFIG.RADIUS * math.cos(math.radians(angle_in_degrees))
            )

            button_name = "Pie_Button" + str(i)  # name of the button not used
            self.btn = create_button(
                name, button_name, pos=(button_pos_x, button_pos_y)
            )

            self.pie_buttons.append(self.btn)

        # Create window control buttons with fixed sizes and actions
        button_widget, minimize_button, close_button = create_window_controls(
            main_window=self, create_button=create_button
        )

    # Button Management
    def update_buttons(self):
        """Update window buttons with current window information."""

        def background_task():
            windows = get_window_list()

            final_button_updates = []

            temp_pie_button_names = (
                self.pie_button_texts
            )  # because the names need to be evaluated here

            for i, window_title in enumerate(windows):
                window_handle = window_handles.get(window_title)
                if not window_handle:  # exclude windows with no handle
                    continue

                app_name = get_application_name(window_title)

                button_title = (
                    window_title
                    if f" - {app_name}" not in window_title
                    else window_title.replace(f" - {app_name}", "")
                )
                button_text = f"{button_title}\n{app_name}"

                ### if windows doesn't already have a button, find a free button for new window ###
                # if the window is already on a button, take the index so it keeps its place
                if window_handle in self.button_window_mapping:
                    button_index = self.button_window_mapping[window_handle]
                else:
                    button_index = None
                    # go through buttons until a free one is found
                    for j in range(CONFIG.MAX_BUTTONS):
                        if temp_pie_button_names[j] == "Empty":
                            button_index = j
                            break
                    if button_index is None:
                        continue  # no free button for you :(

                    self.button_window_mapping[window_handle] = button_index

                temp_pie_button_names[button_index] = button_text

                # print(
                #     f"{temp_pie_button_names[button_index]} has received Index {button_index}.\n"
                # )

                final_button_updates.append(
                    {
                        "index": button_index,
                        "text": button_text,
                        "window_handle": window_handle,
                    }
                )

            # Clean button_window_mapping dict of old windows
            if len(self.button_window_mapping) > 20:
                # Step 1: Extract valid window_handles from button_updates
                valid_window_handles = {
                    update["window_handle"] for update in final_button_updates
                }

                # Step 2: Filter button_window_mapping to only keep pairs where the window_handle is in valid_window_handles
                self.button_window_mapping = {
                    handle: button_id
                    for handle, button_id in self.button_window_mapping.items()
                    if handle in valid_window_handles
                }

            print(self.button_window_mapping)
            # Emit the signal instead of using invokeMethod
            self.update_buttons_signal.emit(final_button_updates)

        threading.Thread(target=background_task, daemon=True).start()

    @pyqtSlot(list)
    def update_button_ui(self, button_updates):
        """Update button UI in the main thread."""
        for update in button_updates:
            button_index = update["index"]
            button_text = update["text"]
            window_handle = update["window_handle"]

            self.pie_button_texts[button_index] = button_text
            self.pie_buttons[button_index].setText(button_text)

            # Disconnect any previous connections first
            try:
                self.pie_buttons[button_index].clicked.disconnect()
            except TypeError:
                pass  # No connections to disconnect

            # Connect new signal
            self.pie_buttons[button_index].clicked.connect(
                lambda checked, hwnd=window_handle: (
                    focus_window_by_handle(hwnd),
                    self.hide(),
                )
            )

        # Clear button attributes when button index not among updates
        for i in range(CONFIG.MAX_BUTTONS):
            if i not in [update["index"] for update in button_updates]:
                self.pie_button_texts[i] = "Empty"
                try:
                    self.pie_buttons[i].clicked.disconnect()
                except TypeError:
                    pass
                self.pie_buttons[i].setText("Empty")

    def customEvent(self, event):
        """Handle the custom event to show the window."""
        if isinstance(event, ShowWindowEvent):
            show_window(
                event.window
            )  # Safely call show_window when the event is posted


def focus_window_by_handle(hwnd):
    """Bring a window to the foreground and restore/maximize as needed."""
    try:
        win32gui.SetForegroundWindow(hwnd)
        placement = win32gui.GetWindowPlacement(hwnd)

        if placement[1] == win32con.SW_MINIMIZE:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        elif placement[1] == win32con.SW_SHOWMAXIMIZED:
            pass
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)

        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"Could not focus window with handle '{hwnd}': {e}")


def show_window(window: QWidget):
    """Display the main window and bring it to the foreground."""
    try:
        # Get the window handle
        hwnd = int(window.winId())

        # Get the current mouse position
        cursor_pos = QCursor.pos()

        # Get screen dimensions
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        screen_left = screen_geometry.left()
        screen_top = screen_geometry.top()
        screen_right = screen_geometry.right()
        screen_bottom = screen_geometry.bottom()

        # Calculate initial new_x and new_y
        new_x = cursor_pos.x() - (window.width() // 2)
        new_y = cursor_pos.y() - (window.height() // 2)

        # Ensure window position stays within screen bounds
        corrected_x = max(screen_left, min(new_x, screen_right - window.width()))
        corrected_y = max(screen_top, min(new_y, screen_bottom - window.height()))

        # Move the window
        window.move(corrected_x, corrected_y)

        # Adjust the cursor position if it was moved
        if new_x != corrected_x or new_y != corrected_y:
            corrected_cursor_x = corrected_x + (window.width() // 2)
            corrected_cursor_y = corrected_y + (window.height() // 2)
            QCursor.setPos(corrected_cursor_x, corrected_cursor_y)

        # Ensure the window is visible and restored
        if not window.isVisible():
            window.show()

        # Get current foreground window and threads
        fg_window = win32gui.GetForegroundWindow()
        fg_thread, _ = win32process.GetWindowThreadProcessId(fg_window)
        this_thread = win32api.GetCurrentThreadId()

        # Detach any previous thread inputs to reset state
        try:
            ctypes.windll.user32.AttachThreadInput(this_thread, fg_thread, False)
        except Exception:
            pass

        # Multiple attempts to bring window to foreground
        for attempt in range(3):
            try:
                # Attach input threads
                ctypes.windll.user32.AttachThreadInput(this_thread, fg_thread, True)

                # Restore window if minimized
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

                # Try multiple methods to bring to foreground
                win32gui.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)

                # Detach input threads
                ctypes.windll.user32.AttachThreadInput(this_thread, fg_thread, False)

                break  # Success, exit attempts
            except Exception as e:
                print(f"Window focus attempt {attempt + 1} failed: {e}")
                time.sleep(0.1)  # Small delay between attempts

        # Final positioning to ensure visibility
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
        )
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            win32con.HWND_NOTOPMOST,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
        )

    except Exception as e:
        print(f"Error showing the main window: {e}")


def listen_for_hotkeys(window: QWidget):
    """Listen for global hotkeys."""

    def wrapper():
        print(
            "Hotkey pressed! Opening switcherino..."
        )  # Debugging: Check if hotkey is detected
        # Post the custom event to the window's event queue
        event = ShowWindowEvent(window)
        # Post the event to the main thread
        QApplication.postEvent(window, event)

    keyboard.add_hotkey(CONFIG.HOTKEY_OPEN, wrapper, suppress=True)
    keyboard.wait()


# Cache Management
def load_cache():
    """Load application name cache from file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache file: {e}")
            return {}
    return {}


def save_cache(cache):
    """Save application name cache to file."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=4)
        print("Cache saved successfully.")
    except Exception as e:
        print(f"Error saving cache file: {e}")


def get_pid_from_window_handle(hwnd):
    """Retrieve the Process ID (PID) for a given window handle."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
    except Exception as e:
        print(f"Error retrieving PID for window: {e}")
        return None


def get_file_description(exe_path):
    """Get the FileDescription (friendly app name) from the executable."""
    try:
        language, codepage = win32api.GetFileVersionInfo(
            exe_path, "\\VarFileInfo\\Translation"
        )[0]
        string_file_info = "\\StringFileInfo\\%04X%04X\\%s" % (
            language,
            codepage,
            "FileDescription",
        )
        description = win32api.GetFileVersionInfo(exe_path, string_file_info)
        return description if description else "Unknown App"
    except Exception as e:
        print(f"Error retrieving file description for {exe_path}: {e}")
        return "Unknown App"


def get_application_name(window_title):
    """Retrieve the application name for a given window title."""
    try:
        window_handle = window_handles.get(window_title)
        if window_handle:
            pid = get_pid_from_window_handle(window_handle)
            if pid:
                process = psutil.Process(pid)
                exe_path = process.exe()
                if os.path.exists(exe_path):
                    exe_name = os.path.basename(exe_path).lower()
                    if exe_name in app_cache:
                        app_name = app_cache[exe_name]
                    else:
                        app_name = get_file_description(exe_path)
                        app_cache[exe_name] = app_name
                        save_cache(app_cache)
                    return app_name
        return window_title
    except Exception as e:
        print(f"Error fetching application name for {window_title}: {e}")
        return "Unknown App, window title: " + window_title


# Window Enumeration and Handling
def get_window_list():
    """Enumerate and retrieve a list of visible windows."""
    local_window_handles = {}

    this_program_hwnd = int(window.winId())

    def enum_windows_callback(hwnd, lparam):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            isCloaked = ctypes.c_int(0)
            ctypes.WinDLL("dwmapi").DwmGetWindowAttribute(
                hwnd, 14, ctypes.byref(isCloaked), ctypes.sizeof(isCloaked)
            )

            if (
                win32gui.IsWindowVisible(hwnd)
                and isCloaked.value == 0
                and window_title.strip()
                and class_name != "Progman"
                and class_name != "AutoHotkeyGUI"
            ):
                if hwnd != this_program_hwnd:
                    local_window_handles[window_title] = hwnd

    try:
        win32gui.EnumWindows(enum_windows_callback, None)
        window_handles.clear()
        window_handles.update(local_window_handles)
        return list(window_handles.keys())
    except Exception as e:
        print(f"Error getting windows: {e}")
        return []


if __name__ == "__main__":
    CACHE_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "app_name_cache.json"
    )
    app_cache = load_cache()

    app = QApplication(sys.argv)

    # Load the stylesheet
    with open("style.qss", "r") as file:
        app.setStyleSheet(file.read())

    # Create and show the main window
    window = PieTaskSwitcherWindow()

    # Show the window briefly and immediately hide it
    window.show()  # Make sure the window is part of the event loop
    # window.hide()  # Hide it right after showing

    # Hotkey Thread
    hotkey_thread = threading.Thread(
        target=listen_for_hotkeys, args=(window,), daemon=True
    )
    hotkey_thread.start()

    # Initial Refresh and Auto-refresh
    # window.refresh()
    window.auto_refresh()

    sys.exit(app.exec())
