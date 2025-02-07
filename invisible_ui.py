import sys
from functools import partial

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from config import CONFIG
from functions.shortcut_utils import open_explorer_window
from functions.taskbar_hide_utils import toggle_taskbar
from functions.window_functions import add_hwnd_to_exclude


class InvisibleUI(QWidget):
    """A clock with no seconds and a 50% transparent background."""

    def __init__(self, obj_name: str = "InvisibleUI", parent=None, button_size: int = 5):
        super().__init__(parent)
        self.obj_name = obj_name
        self.setWindowTitle(f"{CONFIG._PROGRAM_NAME} - InvisibleUI")  # Set the window title
        self.button_size = button_size  # Button size variable

        add_hwnd_to_exclude(self)

        # Set up window properties
        self.setup_window()

        self.button_config = {
            # "btn_btm_left": ((90, self.button_size), partial(open_start_menu, self, hide_parent=False)),
            # "btn_btm_right": ((90, self.button_size), partial(open_action_center, self, hide_parent=False)),
            "btn_btm_center": ((1000, self.button_size), lambda: toggle_taskbar()),
            "btn_ctr_left": ((self.button_size, 600), partial(open_explorer_window, self, hide_parent=False)),
        }

        self.create_buttons()
        self.position_buttons()

        screen = QApplication.primaryScreen()
        screen.geometryChanged.connect(self.handle_geometry_change)

    def create_buttons(self):
        """Initialize buttons with properties."""
        self.buttons = {}
        for name, (size, callback) in self.button_config.items():
            button = QPushButton("", self)
            button.setObjectName("InvisibleButton")
            button.setFixedSize(*size)

            # Rename the callback inside the lambda to avoid conflict
            button.clicked.connect(lambda _, cb=callback: cb())

            setattr(self, name, button)
            self.buttons[name] = button

    def position_buttons(self):
        """Position available buttons dynamically."""
        if "btn_btm_left" in self.buttons:
            self.buttons["btn_btm_left"].move(0, self.height() - self.buttons["btn_btm_left"].height())
        if "btn_btm_right" in self.buttons:
            self.buttons["btn_btm_right"].move(self.width() - self.buttons["btn_btm_right"].width(),
                                               self.height() - self.buttons["btn_btm_right"].height())
        if "btn_btm_center" in self.buttons:
            self.buttons["btn_btm_center"].move(self.width() // 2 - self.buttons["btn_btm_center"].width() // 2,
                                                self.height() - self.buttons["btn_btm_center"].height())

        if "btn_ctr_left" in self.buttons:
            self.buttons["btn_ctr_left"].move(0, self.height() // 2 - self.buttons["btn_ctr_left"].height() // 2)

    def handle_geometry_change(self):
        screen = QApplication.primaryScreen()
        geometry = screen.geometry()

        # Update the main window size based on the screen geometry
        self.setGeometry(0, 0, geometry.width(), geometry.height())

        self.position_buttons()

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

    def on_button_left_clicked(self):
        """Print message when the left button is clicked."""
        print("Left button clicked!")

    def on_button_right_clicked(self):
        """Print message when the right button is clicked."""
        print("Right button clicked!")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the QSS template
    with open("style.qss", "r") as file:
        qss_template = file.read()

    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", CONFIG.ACCENT_COLOR_MUTED)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    app.setStyleSheet(qss)

    invisUI = InvisibleUI()
    invisUI.show()  # Explicitly show the clock widget

    print("Entering event loop...")
    sys.exit(app.exec())  # Start the application event loop
    print("Exited event loop.")
