import sys
from typing import *

from PyQt6.QtCore import (
    Qt,
    QSize,
)
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QApplication, QWidget, QPushButton, QSizePolicy, QSpacerItem

from FontStyle import FontStyle
from ScrollingTextLabel import ScrollingLabel
from config import CONFIG


class PieButton(QPushButton):
    """Custom Button with text animation for long text."""

    def __init__(self,
                 object_name: str,
                 text_1: str = "",
                 text_2: str = "",
                 action: Optional[Callable] = None,
                 fixed_size: bool = True,
                 size: Tuple[int, int] = (CONFIG.BUTTON_WIDTH, CONFIG.BUTTON_HEIGHT),
                 pos: Tuple[int, int] = (0, 0),
                 parent: Optional[QWidget] = None
                 ):
        super().__init__(parent)

        self.setObjectName(object_name)

        # Create a QVBoxLayout for the label
        self.label_layout = QVBoxLayout()
        self.label_layout.setSpacing(0)  # No space between widgets

        # Create a Label (which is on top, when both texts are set
        self.label_1 = ScrollingLabel(text_1, h_align=Qt.AlignmentFlag.AlignLeft, font_style=FontStyle.Normal)
        self.label_layout.addWidget(self.label_1)
        self.label_layout.setContentsMargins(0, 0, 0, 0)

        # Create a second bottom label if text_2 is set
        if text_2 != "":
            self.label_2 = ScrollingLabel(text_2, h_align=Qt.AlignmentFlag.AlignLeft, font_style=FontStyle.Italic)
            self.label_layout.addWidget(self.label_2)

        # Create the main layout for the button (HBoxLayout)
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        # Add a vertical spacer of 50 pixels
        self.spacer = QSpacerItem(30, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout().addSpacerItem(self.spacer)

        # Add the VBoxLayout as a child of the HBoxLayout
        self.layout().addLayout(self.label_layout)

        if fixed_size:
            # Use fixed size if requested or fallback to default size
            self.setFixedSize(QSize(size[0], size[1]))
        else:
            # If no fixed size, button will size to its content
            self.setSizePolicy(
                QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
            )

        try:
            self.clicked.disconnect()
        except TypeError:
            pass  # No existing connections to disconnect

        # Check if action is provided and is callable
        if callable(action):
            self.clicked.connect(action)
        else:
            self.clicked.connect(self.default_action)

        # Set position if provided
        x, y = pos
        # Set position using `move()`, not `setGeometry()`
        self.move(x, y)

    def default_action(self):
        """Default action when no external action is provided."""
        print("There was only the default action assigned.")


def example_function():
    print("Button pressed!")


# Example usage
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the stylesheet
    with open("style.qss", "r") as file:
        app.setStyleSheet(file.read())

    window = QWidget()
    layout = QVBoxLayout(window)

    some_text = "This is a very long text that should scroll smoothly if it doesn't fit in the button."
    some_text_2 = "Short text."
    button = PieButton("button_1", some_text, some_text_2, action=example_function)
    layout.addWidget(button)

    button2 = PieButton("button_2", "Short text.")
    layout.addWidget(button2)

    window.show()
    sys.exit(app.exec())
