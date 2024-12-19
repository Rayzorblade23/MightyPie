import sys

from PyQt6.QtCore import QEvent, Qt, QPoint
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout, QWidget, QSizePolicy


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

        # Get screen size and set window geometry
        screen = QApplication.primaryScreen()
        self.setFixedSize(200,200)

        # Connect signals
        self.child_button.clicked.connect(self.on_child_clicked)

    def resizeEvent(self, event):
        # Center child button in the top-left quadrant
        button_x = (self.width() - self.child_button.width()) // 2
        button_y = (self.height() - self.child_button.height()) // 2
        self.child_button.move(button_x, button_y)

    def check_active_area(self, x, y):
        return x < self.width() // 2 and y < self.height() // 2

    def event(self, event):
        if event.type() == QEvent.Type.HoverMove:
            pos = event.position()
            in_area = self.check_active_area(pos.x(), pos.y())

            if in_area != self.in_active_area:
                self.in_active_area = in_area
                if in_area:
                    self.child_button.setProperty("hovered", True)
                else:
                    self.child_button.setProperty("hovered", False)
                self.child_button.style().unpolish(self.child_button)
                self.child_button.style().polish(self.child_button)
                print("Hover", "enter" if in_area else "leave", "active area")

        elif event.type() == QEvent.Type.MouseButtonPress:
            pos = event.position()
            if self.check_active_area(pos.x(), pos.y()):
                self.is_pressed = True
                self.child_button.setDown(True)
                print("Pressed in active area")
                return True

        elif event.type() == QEvent.Type.MouseButtonRelease:
            if self.is_pressed:
                pos = event.position()
                self.is_pressed = False
                self.child_button.setDown(False)

                if self.check_active_area(pos.x(), pos.y()):
                    self.child_button.click()
                    print("Released in active area - clicked")
                else:
                    print("Released outside active area")
                return True

        elif event.type() == QEvent.Type.Leave:
            if self.in_active_area:
                self.in_active_area = False
                self.child_button.setProperty("hovered", False)
                self.child_button.style().unpolish(self.child_button)
                self.child_button.style().polish(self.child_button)
                if self.is_pressed:
                    self.child_button.setDown(False)
                    self.is_pressed = False
                print("Left window")

        return super().event(event)

    def on_child_clicked(self):
        print("Child button clicked!")

    def is_mouse_near(self, pos: QPoint) -> bool:
        """ Simulate if the mouse is near the AreaButton even outside its boundaries """
        margin = 50  # Define how far outside the button you want to detect
        button_rect = self.rect()
        return button_rect.adjusted(-margin, -margin, margin, margin).contains(pos.toPoint())


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
        area_button = AreaButton("Area Button", self)
        layout.addWidget(area_button)

        # Set the layout to the central widget
        central_widget.setLayout(layout)

        # Set the central widget of the main window
        self.setCentralWidget(central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    stylesheet = ""

    # Load additional styles if needed
    try:
        with open("style_test.qss", "r") as file:
            stylesheet += file.read()
    except FileNotFoundError:
        pass

    app.setStyleSheet(stylesheet)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
