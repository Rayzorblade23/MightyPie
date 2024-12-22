from PyQt6.QtWidgets import QPushButton, QSizePolicy, QWidget
from PyQt6.QtCore import QSize
from typing import Optional, Callable, Tuple

from config import CONFIG


class ExpButton(QPushButton):
    """Class for creating a QPushButton with customizable properties."""

    def __init__(
            self,
            text: str,
            object_name: str,
            action: Optional[Callable] = None,
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

        # Set the button action if provided
        if action:
            self.clicked.connect(action)

        # Set position if provided
        x, y = pos
        # Set position using `move()`, not `setGeometry()`
        self.move(x, y)
