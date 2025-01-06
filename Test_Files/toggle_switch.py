from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, pyqtProperty, QSize
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt6.QtWidgets import QApplication, QPushButton, QLabel, QHBoxLayout, QWidget

from config import CONFIG


class ToggleSwitch(QPushButton):
    def __init__(self, object_name="", size=(46, 28), on_action=None, off_action=None, label_text="", parent=None):
        super().__init__(parent)  # Ensure parent is passed to the QPushButton constructor

        # Set object name
        self.setObjectName(object_name)

        # Set fixed dimensions for the toggle switch button (either from size or default)
        self.setFixedSize(*size)  # Unpack the tuple to set width and height

        self.setCheckable(True)  # Make it act like a toggle switch

        # Define the actions for the two toggle states
        self.on_action = on_action  # Action when toggle is on
        self.off_action = off_action  # Action when toggle is off

        # Define label if provided
        self.label_text = label_text
        self.label = None
        if self.label_text:
            self.label = QLabel(self.label_text)
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the text
            self.label.setFont(QFont('Arial', 10))  # Set font for the label

        # Calculate the circle's size based on the button's height
        self.circle_size_offset = 4
        self.circle_diameter = self.height() - self.circle_size_offset * 2  # 4 pixels smaller than the button height
        self.circle_radius = self.circle_diameter // 2
        self.circle_stroke_width = 2

        self.center_y = self.height() // 2

        # Initial circle position (left side) based on the upper-left anchor
        self._circle_pos = QPoint(self.center_y, self.center_y)

        # Create an animation for the circle's movement
        self.animation = QPropertyAnimation(self, b"circle_pos")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)  # Smooth easing curve

        # Set initial background color for the toggle switch
        self.update_background_color()

        # Connect the button's checked state to trigger animation
        self.clicked.connect(self.toggle_switch)

    @pyqtProperty(QPoint)
    def circle_pos(self):
        """Getter for the circle's position."""
        return self._circle_pos

    @circle_pos.setter
    def circle_pos(self, pos):
        """Setter for the circle's position and trigger a repaint."""
        self._circle_pos = pos
        self.update()  # Trigger the paintEvent to update the drawing

    def paintEvent(self, event):
        """Custom drawing for the toggle switch and circle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw the background of the toggle (rounded rectangle)
        toggle_rect = self.rect()
        painter.setBrush(QBrush(self.background_color))  # Use the current background color
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(toggle_rect, self.height() / 2, self.height() / 2)

        # Draw the circle inside the toggle switch
        painter.setBrush(QBrush(QColor(255, 255, 255)))  # White color for the circle
        painter.setPen(QPen(QColor(128, 128, 128), self.circle_stroke_width))  # Border color of the circle
        painter.drawEllipse(self._circle_pos, self.circle_radius, self.circle_radius)

    def toggle_switch(self):
        """Handles the toggle switch animation based on the button's checked state."""
        if self.isChecked():
            # Move the circle to the right, accounting for the circle's size
            self.animation.setStartValue(self._circle_pos)
            self.animation.setEndValue(
                QPoint(self.width() - self.circle_radius - self.circle_size_offset, self.center_y))  # Correct position for the right side
            # Trigger the "on" action if defined
            if self.on_action:
                self.on_action()
            else:
                print("No action defined for the 'on' state.")
        else:
            # Move the circle to the left, the leftmost position
            self.animation.setStartValue(self._circle_pos)
            self.animation.setEndValue(QPoint(self.center_y, self.center_y))  # Left side
            # Trigger the "off" action if defined
            if self.off_action:
                self.off_action()
            else:
                print("No action defined for the 'off' state.")

        self.animation.start()

        # Update the background color when the toggle state changes
        self.update_background_color()

    def update_background_color(self):
        """Updates the background color of the toggle based on its state."""
        if self.isChecked():
            # Green background when toggled on
            self.background_color = QColor(CONFIG.ACCENT_COLOR)  # Green (#4CAF50)
        else:
            # Gray background when toggled off
            self.background_color = QColor(CONFIG.BG_COLOR)  # Light gray (#ccc)

        self.update()  # Repaint the widget to apply the new background color

    def sizeHint(self):
        """Override sizeHint to accommodate both the toggle and the label."""
        width = self.width() + (self.label.width() if self.label else 0)
        height = max(self.height(), 32)  # Ensure sufficient height for label
        return QSize(width, height)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()

        # Create ToggleSwitch with a label
        toggle = ToggleSwitch(
            on_action=self.on_toggle,
            off_action=None,
            label_text="Enable Feature"
        )

        layout.addWidget(toggle)

        # Add label to layout if it exists
        if toggle.label:
            layout.addWidget(toggle.label)

        self.setLayout(layout)
        self.setWindowTitle("Toggle Switch Example")
        self.show()

    def on_toggle(self):
        print("The toggle is ON!")

    def off_toggle(self):
        print("The toggle is OFF!")


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec()
