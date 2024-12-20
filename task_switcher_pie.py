import math
import threading
from threading import Lock

from PyQt6.QtCore import pyqtSignal, QTimer, QRectF, pyqtSlot, Qt
from PyQt6.QtGui import QMouseEvent, QKeyEvent, QPainter, QBrush, QPen, QColor, QCursor
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QWidget

from config import CONFIG
from events import ShowWindowEvent
from pie_button import PieButton
from pie_indicator_button import DonutSliceButton
from window_controls import create_window_controls
from window_functions import get_filtered_list_of_window_titles, get_application_info, focus_window_by_handle, show_window
from window_manager import WindowManager

manager = WindowManager.get_instance()


class TaskSwitcherPie(QWidget):
    # Add a custom signal for thread-safe updates
    update_buttons_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        # Set the default cursor (normal arrow cursor)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # Set the normal cursor

        # Initialize these attributes BEFORE calling setup methods
        self.inner_circle_main = None
        self.scene = None
        self.view = None
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

    def enterEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))  # Change cursor on hover

    def leaveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # Restore default cursor

    def auto_refresh(self):
        """Automatically monitor and refresh windows periodically in a thread-safe way."""
        # start_time = time.time()

        # Lock access to shared data to ensure thread safety
        with self.button_mapping_lock:
            current_window_titles = get_filtered_list_of_window_titles(self)
            # only actually refresh when windows have opened or closed
            if current_window_titles != self.last_window_titles:
                print("Changed!")
                self.last_window_titles = current_window_titles
                self.refresh()  # Safely call the refresh method to update UI

        # elapsed_time = time.time() - start_time
        # print(f"auto_refresh took {elapsed_time:.3f} seconds")

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
        # Create window control buttons with fixed sizes and actions
        button_widget, minimize_button, close_button = create_window_controls(main_window=self)


        self.donut_button = DonutSliceButton(
            object_name="DonutSlice",
            outer_radius=CONFIG.INNER_RADIUS+30,
            inner_radius=CONFIG.INNER_RADIUS+10,
            start_angle=-22.5,
            span_angle=45,
            action=None,
            pos=(self.rect().center().x(), self.rect().center().y()),
            parent=self
        )

        # # Create and configure the refresh button
        # self.refresh_button = create_button(
        #     label="R",
        #     object_name="refreshButton",
        #     action=self.refresh,
        #     fixed_size=True,
        #     # Using size instead of geometry
        #     size=(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT),
        #     pos=(
        #         (self.triangle_width() - CONFIG.BUTTON_HEIGHT) // 2,
        #         (self.height() - CONFIG.BUTTON_HEIGHT) // 2,
        #     ),  # Using position for x and y
        # )

        # Button Configuration
        # Starting angle

        # Create 8 buttons in a circular pattern, starting with top middle
        for i, pie_button_text in enumerate(self.pie_button_texts):
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
            # self.btn = create_button(name, button_name, pos=(button_pos_x, button_pos_y))

            self.btn = PieButton(
                object_name=button_name,
                text_1=pie_button_text,
                text_2="",
                icon_path="",
                action=None,
                pos=(button_pos_x, button_pos_y),
                parent=self)

            self.pie_buttons.append(self.btn)

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

            temp_pie_button_texts = (
                self.pie_button_texts
            )  # because the names need to be evaluated here

            for window_title in windows_titles:
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

                # Check if the window is already assigned a button
                button_index = self.buttons_To_windows_map.get(window_handle)

                # If Button Index not assigned, find a free button
                if button_index is None:
                    button_index = get_free_button_index(temp_pie_button_texts)
                    # If Button Index still not assigned, no free button for you :(
                    if button_index is None:
                        continue
                    # Assign Button Index to the window handle
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
            print(window_handle)

            self.pie_button_texts[button_index] = button_text_1
            self.pie_buttons[button_index].set_label_1_text(button_text_1)
            self.pie_buttons[button_index].set_label_2_text(button_text_2)
            self.pie_buttons[button_index].update_icon(app_icon_path)

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
            self.pie_buttons[button_index].setEnabled(True)  # Disable the button

        # Clear button attributes when button index not among updates
        for i in range(CONFIG.MAX_BUTTONS):
            if i not in [update["index"] for update in button_updates]:
                self.pie_button_texts[i] = "Empty"
                try:
                    self.pie_buttons[i].clicked.disconnect()
                except TypeError:
                    pass
                self.pie_buttons[i].clicked.connect(
                    lambda checked, hwnd=window_handle: self.hide()
                )
                self.pie_buttons[i].setEnabled(False)  # Disable the button
                self.pie_buttons[i].set_label_1_text("Empty")
                self.pie_buttons[i].set_label_2_text("")
                self.pie_buttons[i].update_icon("")

    def customEvent(self, event):
        """Handle the custom event to show the window."""
        if isinstance(event, ShowWindowEvent):
            self.refresh()
            show_window(event.window)  # Safely call show_window when the event is posted
