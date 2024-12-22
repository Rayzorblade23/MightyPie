import math
import sys
from typing import Tuple

from PyQt6.QtCore import QEvent, Qt, QObject
from PyQt6.QtGui import QMouseEvent, QPainter, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout, QWidget, QSizePolicy

from config import CONFIG

from color_functions import adjust_saturation


class GlobalMouseFilter(QObject):
    def __init__(self, area_button):
        super().__init__()
        self.area_button = area_button  # Reference to the button for state updates

    def eventFilter(self, obj, event):
        if isinstance(event, QMouseEvent):
            global_pos = event.globalPosition().toPoint()

            if event.type() == QEvent.Type.MouseMove:
                self.handle_mouse_move(global_pos)
            elif event.type() == QEvent.Type.MouseButtonPress:
                self.handle_mouse_press(global_pos)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.handle_mouse_release(global_pos)

        return super().eventFilter(obj, event)

    def handle_mouse_move(self, global_pos):
        local_pos = self.area_button.mapFromGlobal(global_pos)
        in_area = self.area_button.check_active_area(local_pos.x(), local_pos.y())

        if in_area != self.area_button.in_active_area:
            self.area_button.in_active_area = in_area
            self.area_button.update_child_button_hover_state(in_area)
            # print("Hover", "enter" if in_area else "leave", "active area")
            self.area_button.set_hover_pos(global_pos)  # Directly pass global position without adjustments

    def handle_mouse_press(self, global_pos):
        local_pos = self.area_button.mapFromGlobal(global_pos)
        if self.area_button.check_active_area(local_pos.x(), local_pos.y()):
            self.area_button.is_pressed = True
            self.area_button.child_button.setDown(True)
            self.area_button.update()  # Request a repaint to show the dot

            # print("Pressed in active area")

    def handle_mouse_release(self, global_pos):
        if self.area_button.is_pressed:
            self.area_button.is_pressed = False
            self.area_button.child_button.setDown(False)

            local_pos = self.area_button.mapFromGlobal(global_pos)
            if self.area_button.check_active_area(local_pos.x(), local_pos.y()):
                self.area_button.child_button.click()
                # print("Released in active area - clicked")
            else:
                print("Released outside active area")


class AreaButton(QPushButton):
    def __init__(self,
                 object_name: str,
                 text="",
                 pos: Tuple[int, int] = (0, 0),
                 offset: Tuple[int, int] = (0, 0),
                 angle_start: float = 0,
                 angle_degrees: float = 45,
                 parent=None):
        super().__init__(text, parent)
        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.angle_start = angle_start
        self.angle_degrees = angle_degrees
        self.offset = offset

        self.child_button = QPushButton("Nyah!", self)
        self.child_button.setFixedSize(80, 80)
        self.in_active_area = False
        self.is_pressed = False
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(100, 100)

        #######################---Dot Functionality---#######################
        # Initialize hover_pos as None
        self.hover_pos = None

        # Flag to control the visibility of dots (debug mode)
        self.show_dots = True  # Set it to True to show dots by default

        # Store a list of all created dot widgets
        self.dot_widgets = []  # List to keep track of all dots
        #####################################################################

        self.child_button.clicked.connect(self.on_child_clicked)

        # Set position if provided
        self.x, self.y = pos
        # Set position using `move()`, not `setGeometry()`
        self.move(self.x - self.width() // 2 + offset[0], self.y - self.height() // 2 + offset[1])

    def paintEvent(self, event):
        super().paintEvent(event)  # Call the base class to handle normal painting

        if self.show_dots and self.hover_pos:
            # Create a new dot widget for each mouse move
            self.create_dot_widget(self.hover_pos)

    def create_dot_widget(self, hover_pos):
        """Creates a new dot widget for each hover position."""
        dot_widget = DotWidget(self.parent())  # Create a new dot widget with PieWindow as parent
        self.dot_widgets.append(dot_widget)  # Add it to the list of dots

        # Convert global position to the parent (PieWindow) coordinate system
        local_pos = self.parent().mapFromGlobal(hover_pos)  # Get position relative to the parent

        dot_widget.move(local_pos)  # Move the dot widget to hover position
        dot_widget.setVisible(True)  # Show the dot widget

    def set_hover_pos(self, pos):
        """Sets the hover position manually from outside the widget."""
        self.hover_pos = pos  # Set hover_pos to the new mouse position
        self.update()  # Ensure the widget is repainted when hover_pos changes


    def resizeEvent(self, event):
        button_x = (self.width() - self.child_button.width()) // 2
        button_y = (self.height() - self.child_button.height()) // 2
        self.child_button.move(button_x, button_y)

    def check_active_area(self, x, y):
        center_x = self.width() // 2 - self.offset[0]
        center_y = self.height() // 2 - self.offset[1]
        dx = x - center_x
        dy = y - center_y

        # Compute angle in degrees (0 to 360)
        theta = math.degrees(math.atan2(dy, dx))
        if theta < 0:
            theta += 360

        # Predefined constants
        angle_end = self.angle_start + self.angle_degrees  # End angle in degrees

        # Check if the angle is within the sector
        if not (
                self.angle_start <= theta <= angle_end if self.angle_start <= angle_end else theta >= self.angle_start or theta <= angle_end):
            return False  # Early exit if angle is outside the sector

        # Compute distance only if angle condition is satisfied
        r = math.sqrt(dx ** 2 + dy ** 2)
        return r >= CONFIG.INNER_RADIUS

    def update_child_button_hover_state(self, hovered):
        self.child_button.setProperty("hovered", hovered)
        self.child_button.style().unpolish(self.child_button)
        self.child_button.style().polish(self.child_button)

    def on_child_clicked(self):
        print("Child button clicked!")

    def set_hover_pos(self, pos):
        """Sets the hover position manually from outside the widget."""
        self.hover_pos = pos
        self.update()  # Ensure the widget is repainted when hover_pos changes


class DotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAutoFillBackground(False)
        self.setFixedSize(10, 10)  # Size of the dot
        self.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(255, 0, 0))  # Red color for the dot
        painter.drawEllipse(0, 0, self.width(), self.height())  # Draw a circle


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the main main_window title and size
        self.setWindowTitle("Main Window with AreaButton")
        self.setGeometry(300, 100, CONFIG.CANVAS_SIZE[0], CONFIG.CANVAS_SIZE[1])  # Initial size of the main_window

        # Create a QWidget to hold the layout
        central_widget = QWidget(self)

        # Create a QHBoxLayout
        layout = QHBoxLayout()

        button_pos_x = int(CONFIG.CANVAS_SIZE[0] / 2)
        button_pos_y = int(CONFIG.CANVAS_SIZE[1] / 2)

        # Create an AreaButton instance and add it to the layout
        self.area_button = AreaButton("Slice!",
                                      "",
                                      pos=(button_pos_x, button_pos_y),
                                      offset=(100, 150),
                                      angle_start=270 - 22.5,
                                      angle_degrees=45,
                                      parent=self)

        # Set the layout to the central widget
        central_widget.setLayout(layout)

        # Set the central widget of the main main_window
        self.setCentralWidget(central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create the main main_window
    window = MainWindow()

    # Install the global mouse filtered_event filter
    global_mouse_filter = GlobalMouseFilter(window.area_button)
    app.installEventFilter(global_mouse_filter)

    # creating hues
    accent_color_muted = adjust_saturation(CONFIG.ACCENT_COLOR, 0.5)

    # Load the QSS template
    with open("style.qss", "r") as file:
        qss_template = file.read()

    # inserting style attributes from the config.py file
    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", accent_color_muted)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    # Apply the QSS to the application or widgets
    app.setStyleSheet(qss)

    window.show()

    sys.exit(app.exec())
