import math
import sys

from PyQt6.QtCore import QEvent, Qt, QObject
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout, QWidget, QSizePolicy


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
            print("Hover", "enter" if in_area else "leave", "active area")

    def handle_mouse_press(self, global_pos):
        local_pos = self.area_button.mapFromGlobal(global_pos)
        if self.area_button.check_active_area(local_pos.x(), local_pos.y()):
            self.area_button.is_pressed = True
            self.area_button.child_button.setDown(True)
            print("Pressed in active area")

    def handle_mouse_release(self, global_pos):
        if self.area_button.is_pressed:
            self.area_button.is_pressed = False
            self.area_button.child_button.setDown(False)

            local_pos = self.area_button.mapFromGlobal(global_pos)
            if self.area_button.check_active_area(local_pos.x(), local_pos.y()):
                self.area_button.child_button.click()
                print("Released in active area - clicked")
            else:
                print("Released outside active area")


class AreaButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setObjectName("area")
        # Create and position the child button
        self.child_button = QPushButton("Click Me", self)
        self.child_button.setFixedSize(30, 30)
        # Initialize states
        self.in_active_area = False
        self.is_pressed = False
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Set fixed size
        self.setFixedSize(200, 200)

        # Connect signals
        self.child_button.clicked.connect(self.on_child_clicked)

    def resizeEvent(self, event):
        # Center child button in the top-left quadrant
        button_x = (self.width() - self.child_button.width()) // 2
        button_y = (self.height() - self.child_button.height()) // 2
        self.child_button.move(button_x, button_y)

    def check_active_area(self, x, y):
        center_x = self.width() // 2
        center_y = self.height() // 2
        dx = x - center_x
        dy = y - center_y

        # Compute angle in degrees (0 to 360)
        theta = math.degrees(math.atan2(dy, dx))
        if theta < 0:
            theta += 360

        # Predefined constants
        d = 100  # Minimum distance
        angle_start = 180 - 22.5  # Start angle in degrees
        angle_end = angle_start + 45  # End angle in degrees

        # Check if the angle is within the sector
        if not (angle_start <= theta <= angle_end if angle_start <= angle_end else theta >= angle_start or theta <= angle_end):
            return False  # Early exit if angle is outside the sector

        # Compute distance only if angle condition is satisfied
        r = math.sqrt(dx ** 2 + dy ** 2)
        return r >= d

        # return x < self.width() // 2 and y < self.height() // 2

    def update_child_button_hover_state(self, hovered):
        self.child_button.setProperty("hovered", hovered)
        self.child_button.style().unpolish(self.child_button)
        self.child_button.style().polish(self.child_button)

    def on_child_clicked(self):
        print("Child button clicked!")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the main window title and size
        self.setWindowTitle("Main Window with AreaButton")
        self.setGeometry(100, 100, 800, 600)  # Initial size of the window

        # Create a QWidget to hold the layout
        central_widget = QWidget(self)

        # Create a QHBoxLayout
        layout = QHBoxLayout()

        # Create an AreaButton instance and add it to the layout
        self.area_button = AreaButton("Area Button", self)
        layout.addWidget(self.area_button)

        # Set the layout to the central widget
        central_widget.setLayout(layout)

        # Set the central widget of the main window
        self.setCentralWidget(central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create the main window
    window = MainWindow()

    # Install the global mouse event filter
    global_mouse_filter = GlobalMouseFilter(window.area_button)
    app.installEventFilter(global_mouse_filter)

    stylesheet = ""

    # Load additional styles if needed
    try:
        with open("style_test.qss", "r") as file:
            stylesheet += file.read()
    except FileNotFoundError:
        pass

    app.setStyleSheet(stylesheet)

    window.show()

    sys.exit(app.exec())
