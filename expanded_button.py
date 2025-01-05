from PyQt6.QtWidgets import QPushButton, QSizePolicy, QWidget
from PyQt6.QtCore import QSize, Qt
from typing import Optional, Callable, Tuple

from config import CONFIG


class ExpandedButton(QPushButton):
    """Class for creating a QPushButton with customizable properties."""

    def __init__(
            self,
            text: str,
            object_name: str,
            left_click_action: Optional[Callable] = None,
            right_click_action: Optional[Callable] = None,
            middle_click_action: Optional[Callable] = None,
            fixed_size: bool = True,
            size: Tuple[int, int] = (CONFIG.BUTTON_WIDTH, CONFIG.BUTTON_HEIGHT),
            pos: Tuple[int, int] = (0, 0),
            parent: Optional[QWidget] = None
    ) -> None:
        """Initializes the QPushButton with optional size, action, and position."""
        super().__init__(text, parent)

        if fixed_size:
            # Use fixed size if requested or fallback to default size
            self.setFixedSize(QSize(size[0], size[1]))
        else:
            # If no fixed size, button will size to its content
            self.setSizePolicy(
                QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
            )

        self.setObjectName(object_name)

        # Store the provided actions
        self.left_click_action = left_click_action
        self.right_click_action = right_click_action
        self.middle_click_action = middle_click_action

        # Set position if provided
        x, y = pos
        self.move(x, y)

    def mousePressEvent(self, event) -> None:
        """Override mouse press event to handle different buttons."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Handle left-click
            if self.left_click_action:
                self.left_click_action(event)
            else:
                print("Left-click detected! No action provided.")

        elif event.button() == Qt.MouseButton.RightButton:
            # Handle right-click
            if self.right_click_action:
                self.right_click_action(event)
            else:
                print("Right-click detected! No action provided.")

        elif event.button() == Qt.MouseButton.MiddleButton:
            # Handle middle-click
            if self.middle_click_action:
                self.middle_click_action(event)
            else:
                print("Middle-click detected! No action provided.")

        # Call the parent class's method to ensure normal handling (optional)
        super().mousePressEvent(event)
