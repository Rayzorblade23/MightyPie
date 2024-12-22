import math
import threading
from threading import Lock

from PyQt6.QtCore import pyqtSignal, QTimer, QRectF, pyqtSlot, Qt
from PyQt6.QtGui import QPainter, QBrush, QPen, QColor
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsView, QGraphicsScene, QWidget, QPushButton
from PyQt6.uic.properties import QtCore

from area_button import AreaButton
from config import CONFIG
from donut_slice_button import DonutSliceButton
from exp_button import ExpButton
from pie_button import PieButton
from window_functions import get_filtered_list_of_window_titles, get_application_info, focus_window_by_handle
from window_manager import WindowManager

manager = WindowManager.get_instance()

import time


class PieMenuTaskSwitcher(QWidget):
    # Add a custom signal for thread-safe updates
    update_buttons_signal = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize these attributes BEFORE calling setup methods
        self.donut_button = None
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

        self.setup_window()  # Configure main_window properties
        # Create scene and graphical elements
        self.setup_scene_and_view()
        # Create all buttons (task and main_window controls)
        self.setup_buttons()

        # Start auto-refreshing every REFRESH_INTERVAL milliseconds
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        self.auto_refresh_timer.start(CONFIG.REFRESH_INTERVAL)  # Periodic refresh

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

    def setup_window(self):
        """Set up the main main_window properties."""
        self.setWindowTitle("PieTaskSwitcher")
        # Non-resizable main_window
        self.setFixedSize(CONFIG.RADIUS * 2 + CONFIG.BUTTON_WIDTH * 2, CONFIG.RADIUS * 2 + CONFIG.BUTTON_HEIGHT * 2)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def setup_scene_and_view(self):
        """Set up the scene and graphical elements."""
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.view.setObjectName("PieMenuTaskSwitcher")

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
                self.rect().center().x() - CONFIG.INNER_RADIUS,  # Adjust for radius
                self.rect().center().y() - CONFIG.INNER_RADIUS,  # Adjust for radius
                CONFIG.INNER_RADIUS * 2,  # Diameter
                CONFIG.INNER_RADIUS * 2  # Diameter
            )
        )
        self.inner_circle_main.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.inner_circle_main.setPen(QPen(QColor(30, 30, 30), 7))
        self.scene.addItem(self.inner_circle_main)

        # Create another circle for the outline (slightly thicker)
        self.outline_circle = SmoothCircle(
            QRectF(
                self.rect().center().x() - CONFIG.INNER_RADIUS,  # Adjust for radius
                self.rect().center().y() - CONFIG.INNER_RADIUS,  # Adjust for radius
                CONFIG.INNER_RADIUS * 2,  # Diameter
                CONFIG.INNER_RADIUS * 2  # Diameter
            )
        )
        self.outline_circle.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.outline_circle.setPen(QPen(QColor(50, 50, 50), 9))

        self.outline_circle.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.inner_circle_main.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        # Add the circles to the scene
        self.scene.addItem(self.outline_circle)
        self.scene.addItem(self.inner_circle_main)

        # Ensure the inner circle is on top by setting its Z-index higher than the outline circle
        self.inner_circle_main.setZValue(1)  # Higher Z-value to be in front
        self.outline_circle.setZValue(0)  # Lower Z-value to be behind

    def setup_buttons(self):
        """Create and position all buttons."""

        self.donut_button = DonutSliceButton(
            object_name="DonutSlice",
            outer_radius=CONFIG.INNER_RADIUS + 30,
            inner_radius=CONFIG.INNER_RADIUS + 10,
            start_angle=-22.5,
            span_angle=45,
            action=None,
            pos=(self.rect().center().x(), self.rect().center().y()),
            parent=self
        )
        self.donut_button.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # # Create and configure the refresh button
        # self.refresh_button = ExpButton(
        #     text="",
        #     object_name="refreshButton",
        #     action=lambda checked: print("What"),
        #     fixed_size=True,
        #     # Using size instead of geometry
        #     size=(CONFIG.INNER_RADIUS * 2, CONFIG.INNER_RADIUS * 2),
        #     pos=(self.width() // 2 - CONFIG.INNER_RADIUS, self.height() // 2 - CONFIG.INNER_RADIUS)  # Using position for x and y
        # )
        # self.refresh_button.setParent(self)
        # self.refresh_button.lower()
        # self.view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


        # Creates the area button that has the screen spanning pie sections
        self.area_button = AreaButton("Slice!",
                                      "",
                                      pos=(self.width() // 2, self.height() // 2),
                                      parent=self)
        # Make the actual button click-through
        self.area_button.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

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
            button_pos_x = int(self.width() / 2 + offset_x + CONFIG.RADIUS * math.sin(math.radians(angle_in_degrees)))
            button_pos_y = int(self.height() / 2 - offset_y - CONFIG.RADIUS * math.cos(math.radians(angle_in_degrees)))

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

    def update_child_button_hover_state(self, button, hovered):
        button.setProperty("hovered", hovered)
        button.style().unpolish(button)
        button.style().polish(button)

    # Button Management
    def update_buttons(self):
        """Update main_window buttons with current main_window information."""

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

                # Check if the main_window is already assigned a button
                button_index = self.buttons_To_windows_map.get(window_handle)

                # If Button Index not assigned, find a free button
                if button_index is None:
                    button_index = get_free_button_index(temp_pie_button_texts)
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
                    QTimer.singleShot(100, lambda: focus_window_by_handle(hwnd)),  # Delay in event loop
                    self.parent().hide(),
                )
            )
            # self.pie_buttons[button_index].setEnabled(True)

        # Clear button attributes when button index not among updates
        for i in range(CONFIG.MAX_BUTTONS):
            if i not in [update["index"] for update in button_updates]:
                self.pie_button_texts[i] = "Empty"
                try:
                    self.pie_buttons[i].clicked.disconnect()
                except TypeError:
                    pass
                # self.pie_buttons[i].clicked.connect(
                #     lambda checked: (
                #         self.parent().hide(),
                #     )
                # )
                # self.pie_buttons[i].setEnabled(False)  # Disable the button
                self.pie_buttons[i].set_label_1_text("Empty")
                self.pie_buttons[i].set_label_2_text("")
                self.pie_buttons[i].update_icon("")
