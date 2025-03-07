from functools import partial

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from src.data.button_functions import ButtonFunctions
from src.data.config import CONFIG
from src.utils.shortcut_utils import open_explorer_window
from src.utils.taskbar_hide_utils import toggle_taskbar
from src.utils.window_utils import add_hwnd_to_exclude


class InvisibleUI(QWidget):
    """A clock with no seconds and a 50% transparent background."""

    def __init__(self, obj_name: str = "InvisibleUI", parent=None, button_size: int = 6):
        super().__init__(parent)
        self.obj_name = obj_name
        self.setWindowTitle(f"{CONFIG.INTERNAL_PROGRAM_NAME} - InvisibleUI")  # Set the window title
        self.button_size = button_size  # Button size variable

        self.button_functions = ButtonFunctions()

        add_hwnd_to_exclude(self)

        # Set up window properties
        self.setup_window()

        self.button_config = {
            "button_bottom_center": ((1000, self.button_size), lambda: toggle_taskbar()),
            "button_center_left": ((self.button_size, self.height() // 3), partial(open_explorer_window, self, hide_parent=False)),
            # "button_center_right": ((self.button_size, self.height() // 3), self.button_functions.get_function("clipboard")["action"]),
        }

        self.create_buttons()
        self.position_buttons()

    def create_buttons(self):
        """Initialize buttons with properties."""
        self.buttons = {}
        for name, (size, callback) in self.button_config.items():
            button = QPushButton("", self)
            button.setObjectName("InvisibleButton")
            button.setFixedSize(*size)

            # print(callback)
            # Rename the callback inside the lambda to avoid conflict
            button.clicked.connect(lambda _, cb=callback: cb())

            setattr(self, name, button)
            self.buttons[name] = button

    def position_buttons(self):
        """Position available buttons dynamically."""
        if "button_bottom_center" in self.buttons:
            bottom_x = self.width() // 2 - self.buttons["button_bottom_center"].width() // 2
            bottom_y = self.height() - self.buttons["button_bottom_center"].height()
            self.buttons["button_bottom_center"].move(bottom_x, bottom_y)

        if "button_center_left" in self.buttons:
            left_x = 0
            left_y = self.height() // 2 - self.buttons["button_center_left"].height() // 2
            self.buttons["button_center_left"].move(left_x, left_y)

        ###### Doesn't work reliably on the right edge with monitor scaling
        # if "button_center_right" in self.buttons:
        #     right_x = self.width() - self.buttons["button_center_right"].width()  # Align to the right edge
        #     right_y = self.height() // 4 - self.buttons["button_center_right"].height() // 2  # Center vertically
        #     self.buttons["button_center_right"].move(right_x, right_y)

    def setup_window(self):
        """Set up the main window properties."""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Keep window background transparent
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)

        # Resize the window to half screen width (half of the screen width, full screen height)
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height() + 1)  # Full height, half width

    def resizeEvent(self, event):
        """Reposition buttons when the window is resized."""
        super().resizeEvent(event)
        self.position_buttons()
    #
    # @staticmethod
    # def on_button_left_clicked():
    #     """Print message when the left button is clicked."""
    #     print("Left button clicked!")
    #
    # @staticmethod
    # def on_button_right_clicked():
    #     """Print message when the right button is clicked."""
    #     print("Right button clicked!")
