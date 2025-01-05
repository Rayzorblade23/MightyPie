from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QPushButton, QSizePolicy
from config import CONFIG

class ExpandedButton(QPushButton):
    """Class for creating a QPushButton with customizable properties."""

    left_clicked = pyqtSignal()  # Signal for left-click
    right_clicked = pyqtSignal()  # Signal for right-click
    middle_clicked = pyqtSignal()  # Signal for middle-click

    def __init__(self, text, object_name, fixed_size=True, size=(CONFIG.BUTTON_WIDTH, CONFIG.BUTTON_HEIGHT),
                 pos=(0, 0), parent=None):
        super().__init__(text, parent)
        self.setObjectName(object_name)

        if fixed_size:
            self.setFixedSize(QSize(size[0], size[1]))
        else:
            self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        x, y = pos
        self.move(x, y)

        # Initialize the "hovered" property to false
        self.setProperty("hovered", False)
        self.setProperty("pressed", False)  # Initialize pressed state

    def enterEvent(self, event) -> None:
        """Handle mouse entering the button area (hover state)."""
        self.setProperty("hovered", True)  # Set the hovered property to true
        self.style().unpolish(self)  # Unpolish to force a re-evaluation of the style
        self.style().polish(self)  # Polish to apply the new style

    def leaveEvent(self, event) -> None:
        """Handle mouse leaving the button area (reset to normal state)."""
        self.setProperty("hovered", False)  # Set the hovered property to false
        self.style().unpolish(self)  # Unpolish to force a re-evaluation of the style
        self.style().polish(self)  # Polish to apply the new style

    def mousePressEvent(self, event) -> None:
        """Handle mouse press event to show pressed state."""
        # Set the "pressed" property to true (which is needed in the QSS for styling)
        self.setProperty("pressed", True)
        self.style().unpolish(self)  # Unpolish to force a re-evaluation of the style
        self.style().polish(self)  # Polish to apply the new style
        if event.button() == Qt.MouseButton.LeftButton:
            # Emit the left-click signal
            self.left_clicked.emit()

        elif event.button() == Qt.MouseButton.RightButton:
            # Emit the right-click signal
            self.right_clicked.emit()

        elif event.button() == Qt.MouseButton.MiddleButton:
            # Emit the middle-click signal
            self.middle_clicked.emit()


    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release event to reset to normal or hover state."""
        # Reset the "pressed" property to false when the button is released
        self.setProperty("pressed", False)
        self.style().unpolish(self)  # Unpolish to force a re-evaluation of the style
        self.style().polish(self)  # Polish to apply the new style
