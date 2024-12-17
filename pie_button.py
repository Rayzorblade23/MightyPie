import sys
from typing import *

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QVBoxLayout, QApplication, QWidget, QPushButton, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy

from config import CONFIG
from font_styles import FontStyle
from scrolling_text_label import ScrollingLabel


class PieButton(QPushButton):
    """Custom Button with text animation for long text."""

    def __init__(self,
                 object_name: str,
                 text_1: str = "",
                 text_2: str = "",
                 icon_path: str = "",
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
        # self.label_layout.setSpacing(0)  # No space between widgets

        # Create a Label (which is on top, when both texts are set
        self.label_1 = ScrollingLabel(text_1, h_align=Qt.AlignmentFlag.AlignLeft, font_style=FontStyle.Normal)
        self.label_1.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.label_layout.addWidget(self.label_1)
        self.label_layout.setContentsMargins(0, 0, 0, 0)

        # Create a second bottom label if text_2 is set
        if text_2 != "":
            self.label_2 = ScrollingLabel(text_2, h_align=Qt.AlignmentFlag.AlignLeft, font_style=FontStyle.Italic)
            self.label_2.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.label_layout.addWidget(self.label_2)

        # Create the main layout for the button (HBoxLayout)
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)  # Set minimal spacing between widgets

        self.update_icon(icon_path)

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
        print(f"There was only the default action assigned for {self.objectName()}")

    def set_label_1_text(self, text: str):
        """Change the text of label_1 from outside."""
        self.label_1.update_text(text)

    def set_label_2_text(self, text: str):
        """Change the text of label_2 from outside."""
        if text:  # If text is not empty or None
            if hasattr(self, 'label_2'):  # Check if label_2 already exists
                self.label_2.update_text(text)
            else:
                # Create label_2 dynamically
                self.label_2 = ScrollingLabel(text, h_align=Qt.AlignmentFlag.AlignLeft, font_style=FontStyle.Italic)
                self.label_2.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                # Add label_2 to the layout
                self.label_layout.addWidget(self.label_2)

                # Force layout to update
                self.label_layout.update()
        else:  # If text is empty or None, remove label_2
            if hasattr(self, 'label_2'):
                # Remove label_2 from the layout
                self.label_layout.removeWidget(self.label_2)
                self.label_2.deleteLater()  # Safely delete the widget
                del self.label_2  # Delete the attribute to avoid future references

    def update_icon(self, app_icon_path=None):
        """Add or remove an icon and spacer in the given layout based on the provided icon path."""
        # Remove existing icon and spacer if present
        existing_spacer = None
        existing_icon_label = None

        # Iterate through layout items to find existing spacer or icon label
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            widget = item.widget()
            if isinstance(widget, QLabel):  # Check for QLabel
                existing_icon_label = widget
            elif isinstance(item, QSpacerItem):  # Check for spacer
                existing_spacer = item

        # Remove existing icon label
        if existing_icon_label:
            self.layout().removeWidget(existing_icon_label)
            existing_icon_label.deleteLater()

        # Remove existing spacer
        if existing_spacer:
            self.layout().removeItem(existing_spacer)

        # Add new icon and spacer if an icon path is provided
        if app_icon_path:
            spacer = QSpacerItem(CONFIG.PIE_TEXT_LABEL_MARGINS, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            self.layout().insertItem(0, spacer)

            # Load the icon from the file path
            icon = QPixmap(app_icon_path)

            # Check if the icon is valid
            if not icon.isNull():
                icon_label = QLabel()
                icon_label.setPixmap(icon.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                                 Qt.TransformationMode.SmoothTransformation))  # Adjust size as needed
                icon_label.setFixedSize(16, CONFIG.BUTTON_HEIGHT)  # Adjust size to match your icon dimensions
                icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

                self.layout().insertWidget(1, icon_label)


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

    icon_path = "D:\Mind-Portal\Multi-Media\Icons\music.png"
    button2 = PieButton("button_2", "Short text.", icon_path=icon_path)
    layout.addWidget(button2)

    window.show()
    sys.exit(app.exec())
