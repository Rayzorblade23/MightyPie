from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QPushButton, QSizePolicy
from data.config import CONFIG

class ExpandedButton(QPushButton):
    """Class for creating a QPushButton with customizable properties."""

    left_clicked = pyqtSignal()  # Signal for left-click
    right_clicked = pyqtSignal()  # Signal for right-click
    middle_clicked = pyqtSignal()  # Signal for middle-click

    def __init__(self, text, object_name, fixed_size=True, size=(CONFIG._BUTTON_WIDTH, CONFIG._BUTTON_HEIGHT),
                 pos=(0, 0), parent=None):
        super().__init__(text, parent)
        self.setObjectName(object_name)

        if fixed_size:
            self.setFixedSize(QSize(size[0], size[1]))
        else:
            self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        x, y = pos
        self.move(x, y)

    def mousePressEvent(self, event):
        """Handle mouse press events (left, right, middle)."""
        # Ensure that the button is marked as "pressed" (i.e., visually pressed)
        self.setDown(True)
        super().mousePressEvent(event)  # Ensure default QPushButton press behavior is called

    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.left_clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.middle_clicked.emit()
        # Ensure the default behavior is maintained (like styling updates)
        super().mouseReleaseEvent(event)  # This calls the default QPushButton release behavior

        # After releasing the mouse button, reset the "pressed" state
        self.setDown(False)  # This removes the "pressed" visual state

    def enterEvent(self, event):
        """Handle mouse enter event."""
        super().enterEvent(event)  # Default hover behavior (handled by Qt automatically)

    def leaveEvent(self, event):
        """Handle mouse leave event."""
        super().leaveEvent(event)  # Default leave behavior (handled by Qt automatically)

