import logging

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QPushButton, QSizePolicy

from src.data.config import CONFIG

logger = logging.getLogger(__name__)


class ExpandedButton(QPushButton):
    """Class for creating a QPushButton with customizable properties."""

    left_clicked = pyqtSignal()  # Signal for left-click
    right_clicked = pyqtSignal()  # Signal for right-click
    middle_clicked = pyqtSignal()  # Signal for middle-click

    def __init__(self, text, object_name, fixed_size=True, size=(CONFIG.INTERNAL_BUTTON_WIDTH, CONFIG.INTERNAL_BUTTON_HEIGHT),
                 pos=(0, 0), parent=None):
        super().__init__(text, parent)
        self.setObjectName(object_name)

        self.set_size(fixed_size, size)

        self.set_pos(pos)

    def set_pos(self, pos):
        x, y = pos
        self.move(x, y)

    def set_size(self, fixed_size, size):
        if fixed_size:
            self.setFixedSize(QSize(size[0], size[1]))
        else:
            self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

    def mousePressEvent(self, event):
        """Handle mouse press events (left, right, middle)."""
        # Ensure that the button is marked as "pressed" (i.e., visually pressed)
        self.setDown(True)
        super().mousePressEvent(event)  # Ensure default QPushButton press behavior is called

    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.MouseButton.LeftButton:
            logger.debug(f"'{self.objectName()}' left-clicked")
            self.left_clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            logger.debug(f"'{self.objectName()}' right-clicked")
            self.right_clicked.emit()
        elif event.button() == Qt.MouseButton.MiddleButton:
            logger.debug(f"'{self.objectName()}' middle-clicked")
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
