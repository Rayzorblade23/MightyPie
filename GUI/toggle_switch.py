from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, pyqtProperty, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout

from config import CONFIG


class Toggle(QPushButton):
    def __init__(self, size=(46, 28), on_action=None, off_action=None, parent=None, cooldown_ms=300):
        super().__init__(parent)
        self.setObjectName("Toggle")

        # Define actions
        self.on_action = on_action
        self.off_action = off_action

        # Set cooldown time in milliseconds (default 500ms)
        self.cooldown_ms = cooldown_ms
        self._is_clickable = True  # Flag to track if the button can be clicked

        # Set size of the taskbar_toggle button
        self.setFixedSize(*size)
        self.setCheckable(True)  # Make it a taskbar_toggle button

        # Circle settings
        self.circle_size_offset = 4
        self.circle_diameter = self.height() - self.circle_size_offset * 2
        self.circle_radius = self.circle_diameter // 2
        self.circle_stroke_width = 2
        self.center_y = self.height() // 2
        self._circle_pos = QPoint(self.center_y, self.center_y)

        # Create the animation for the taskbar_toggle
        self.animation = QPropertyAnimation(self, b"circle_pos")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Connect the button's checked state to taskbar_toggle action
        self.clicked.connect(self.toggle_switch)

        # Set initial background color
        self.update_background_color()

    @pyqtProperty(QPoint)
    def circle_pos(self):
        return self._circle_pos

    @circle_pos.setter
    def circle_pos(self, pos):
        self._circle_pos = pos
        self.update()  # Trigger the paintEvent to redraw

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw the background of the taskbar_toggle (rounded rectangle)
        toggle_rect = self.rect()
        painter.setBrush(QBrush(self.background_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(toggle_rect, self.height() / 2, self.height() / 2)

        # Set circle color based on the enabled state
        if self.isEnabled():
            circle_color = QColor(255, 255, 255)  # White color for the circle when enabled
            border_color = QColor(128, 128, 128)  # Border color when enabled
        else:
            circle_color = QColor(150, 150, 150)  # Gray color for the circle when disabled
            border_color = QColor(100, 100, 100)  # Border color when disabled

        # Draw the circle inside the toggle switch
        painter.setBrush(QBrush(circle_color))
        painter.setPen(QPen(border_color, self.circle_stroke_width))
        painter.drawEllipse(self._circle_pos, self.circle_radius, self.circle_radius)

    def toggle_switch(self):
        if not self._is_clickable:
            return  # Ignore click if button is in cooldown state

        # Set the button to non-clickable (cooldown state)
        self._is_clickable = False
        self.setDisabled(True)  # Optionally disable the button to prevent further clicks

        # Start the taskbar_toggle animation
        if self.isChecked():
            # Move the circle to the right
            self.animation.setStartValue(self._circle_pos)
            self.animation.setEndValue(
                QPoint(self.width() - self.circle_radius - self.circle_size_offset, self.center_y))
            if self.on_action:
                self.on_action()
        else:
            # Move the circle to the left
            self.animation.setStartValue(self._circle_pos)
            self.animation.setEndValue(QPoint(self.center_y, self.center_y))
            if self.off_action:
                self.off_action()

        self.animation.start()
        self.update_background_color()

        # Set up a timer to reset the cooldown after the specified time
        QTimer.singleShot(self.cooldown_ms, self.reset_cooldown)  # Reset after cooldown period

    def reset_cooldown(self):
        # Re-enable the button and make it clickable again
        self._is_clickable = True
        self.setEnabled(True)

    def update_background_color(self):
        if self.isChecked():
            self.background_color = QColor(CONFIG.ACCENT_COLOR_MUTED)  # Green
        else:
            self.background_color = QColor(CONFIG.BG_COLOR)  # Gray
        self.update()


class ToggleSwitch(QWidget):
    def __init__(self, object_name="", size=(CONFIG.BUTTON_HEIGHT, int(CONFIG.BUTTON_HEIGHT * 4 / 7)), on_action=None, off_action=None, label_text="", parent=None):
        super().__init__(parent)

        # Set the object name
        self.setObjectName(object_name)

        # Create the container widget to hold both the taskbar_toggle and the label
        self.container = QWidget(self)
        container_layout = QHBoxLayout()  # Horizontal layout for the container

        # Set the layout to the container
        self.container.setLayout(container_layout)

        # Create the taskbar_toggle button (QPushButton)
        self.toggle = Toggle(size=size, on_action=on_action, off_action=off_action, parent=self.container)

        # Create label if provided
        self.label = None
        if label_text:
            self.label = QLabel(label_text, self.container)
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.label.setFont(QFont('Arial', 10))

        # Add the taskbar_toggle button and label (if any) to the container's layout
        self.container.layout().addWidget(self.toggle)

        container_layout.addSpacing(2)  # Adds space between the toggle and label

        if self.label:
            self.container.layout().addWidget(self.label)

        # Ensure the container resizes correctly based on its children
        self.container.adjustSize()  # Optional: Ensure the container adjusts to its content size

    def sizeHint(self):
        return self.container.sizeHint()  # Make sure the main widget returns the size of the container


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Main layout for the window
        layout = QVBoxLayout()

        # Create the ToggleSwitch with a label
        toggle = ToggleSwitch(
            on_action=self.on_toggle,
            off_action=self.off_toggle,
            label_text="Enable Feature"
        )

        # Add the ToggleSwitch widget to the layout
        layout.addWidget(toggle)

        self.setLayout(layout)
        self.setWindowTitle("Toggle Switch Example")
        self.show()

    def on_toggle(self):
        print("The taskbar_toggle is ON!")

    def off_toggle(self):
        print("The taskbar_toggle is OFF!")


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec()
