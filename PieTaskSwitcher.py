import math
import sys
import threading
import time
from threading import Lock

import keyboard
from PyQt6.QtCore import (
    Qt,
    QRectF,
    QTimer,
    QEvent,
    QSize,
    pyqtSlot,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QBrush,
    QPen,
    QPainter,
    QMouseEvent,
    QKeyEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsEllipseItem,
    QPushButton,
    QSizePolicy,
)

from config import CONFIG
from window_controls import create_window_controls
from window_functions import focus_window_by_handle, get_application_name, get_filtered_list_of_window_titles, show_window
from window_manager import WindowManager


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
        self.btn = None
        self.buttons_To_windows_map = {}
        self.button_mapping_lock = Lock()
        self.pie_button_texts = ["Empty" for _ in range(CONFIG.MAX_BUTTONS)]
        self.pie_buttons = []
        self.last_window_titles = []

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
            current_window_titles = get_filtered_list_of_window_titles(self)
            # only actually refresh when windows have opened or closed
            if current_window_titles != self.last_window_titles:
                self.last_window_titles = current_window_titles
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
            button_pos_x = int(CONFIG.CANVAS_SIZE[0] / 2 + offset_x + CONFIG.RADIUS * math.sin(math.radians(angle_in_degrees)))
            button_pos_y = int(CONFIG.CANVAS_SIZE[1] / 2 - offset_y - CONFIG.RADIUS * math.cos(math.radians(angle_in_degrees)))

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

        def get_free_button_index(temp_pie_button_names):
            """Find a free button index in the button names list."""
            for j in range(CONFIG.MAX_BUTTONS):
                if temp_pie_button_names[j] == "Empty":
                    return j
            return None

        def background_task():
            windows_titles = get_filtered_list_of_window_titles(self)

            final_button_updates = []

            temp_pie_button_names = (
                self.pie_button_texts
            )  # because the names need to be evaluated here

            for window_title in windows_titles:
                window_handle = manager.get_window_titles_to_hwnds_map().get(window_title)
                if not window_handle:  # Exclude windows with no handle
                    continue

                app_name = get_application_name(window_handle)

                button_title = (
                    window_title
                    if f" - {app_name}" not in window_title
                    else window_title.replace(f" - {app_name}", "")
                )
                button_text = f"{button_title}\n {app_name}"

                # Check if the window is already assigned a button
                button_index = self.buttons_To_windows_map.get(window_handle)

                # If Button Index not assigned, find a free button
                if button_index is None:
                    button_index = get_free_button_index(temp_pie_button_names)
                    # If Button Index still not assigned, no free button for you :(
                    if button_index is None:
                        continue
                    # Assign Button Index to the window handle
                    self.buttons_To_windows_map[window_handle] = button_index

                temp_pie_button_names[button_index] = button_text  # Update button name

                final_button_updates.append(
                    {
                        "index": button_index,
                        "text": button_text,
                        "window_handle": window_handle,
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
            show_window(event.window)  # Safely call show_window when the event is posted


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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the stylesheet
    with open("style.qss", "r") as file:
        app.setStyleSheet(file.read())

    manager = WindowManager.get_instance()

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
