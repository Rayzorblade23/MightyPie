from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QPushButton, QSizePolicy

from config import CONFIG


class ExpandedButton(QPushButton):
    """Class for creating a QPushButton with customizable properties."""

    left_clicked = pyqtSignal()  # Signal for left-click
    right_clicked = pyqtSignal()  # Signal for right-click
    middle_clicked = pyqtSignal()  # Signal for middle-click

    def __init__(self, text, object_name, left_click_action=None, right_click_action=None, middle_click_action=None, fixed_size=True,
                 size=(CONFIG.BUTTON_WIDTH, CONFIG.BUTTON_HEIGHT), pos=(0, 0), parent=None):
        super().__init__(text, parent)
        self.setObjectName(object_name)

        if fixed_size:
            self.setFixedSize(QSize(size[0], size[1]))
        else:
            self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.left_click_action = left_click_action
        self.right_click_action = right_click_action
        self.middle_click_action = middle_click_action

        x, y = pos
        self.move(x, y)

    def mousePressEvent(self, event) -> None:
        """Override mouse press event to handle different buttons."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Emit the left-click signal
            self.left_clicked.emit()
            if self.left_click_action:
                self.left_click_action(event)

        elif event.button() == Qt.MouseButton.RightButton:
            # Emit the right-click signal
            self.right_clicked.emit()
            if self.right_click_action:
                self.right_click_action(event)

        elif event.button() == Qt.MouseButton.MiddleButton:
            # Emit the middle-click signal
            self.middle_clicked.emit()
            if self.middle_click_action:
                self.middle_click_action(event)

        super().mousePressEvent(event)
