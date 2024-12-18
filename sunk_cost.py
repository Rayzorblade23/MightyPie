import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainter, QColor, QPolygonF


class TriangleButton(QPushButton):
    """Custom button that displays a triangle shape."""

    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.message = message  # Store the message for this button
        self.clicked.connect(self.on_clicked)

    def paintEvent(self, event):
        """Paints the triangle shape on the button."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set button background color
        painter.setBrush(QColor(100, 100, 255))  # Blue color
        painter.setPen(QColor(255, 255, 255))  # White border

        # Define triangle points
        triangle = QPolygonF([
            QPointF(self.width() / 2, 0),  # Top point
            QPointF(0, self.height()),  # Bottom-left point
            QPointF(self.width(), self.height())  # Bottom-right point
        ])

        painter.drawPolygon(triangle)
        painter.end()

    def on_clicked(self):
        """Handle button click and print the message."""
        print(self.message)


class HexagonalLayout(QWidget):
    """Window with a hexagonal pattern of triangle buttons."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hexagon of Triangular Buttons")
        self.showFullScreen()  # Make the window cover the entire screen

        # Hexagon button labels/messages
        button_messages = [
            "Button 1", "Button 2", "Button 3",
            "Button 4", "Button 5", "Button 6"
        ]

        # Create the buttons and store them
        self.buttons = []
        for i, message in enumerate(button_messages):
            button = TriangleButton(message)
            self.buttons.append(button)

        # Adjust button size
        button_size = 150  # Button size

        for button in self.buttons:
            button.setFixedSize(button_size, button_size)

        # Set layout to None, we will manage the positions ourselves
        self.setLayout(None)

        # Arrange the buttons
        self.arrange_buttons(button_size)

    def arrange_buttons(self, button_size):
        """Arrange the buttons in a hexagonal pattern."""
        # Define spacing values for the hexagonal pattern
        vertical_spacing = button_size * 0.75  # Height of the triangle is ~0.75 of the width
        horizontal_spacing = button_size * 1.5  # Spacing between columns

        # Calculate positions for buttons to form a hexagon
        positions = [
            (0, 0),  # Button 1
            (horizontal_spacing, 0),  # Button 2
            (horizontal_spacing * 2, 0),  # Button 3
            (horizontal_spacing / 2, vertical_spacing),  # Button 4
            (horizontal_spacing * 1.5, vertical_spacing),  # Button 5
            (horizontal_spacing, vertical_spacing * 2),  # Button 6
        ]

        for i, button in enumerate(self.buttons):
            x, y = positions[i]
            button.move(int(x), int(y))  # Convert float to int
            self.layout().addWidget(button)  # Add button to layout


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HexagonalLayout()
    window.show()
    sys.exit(app.exec())
