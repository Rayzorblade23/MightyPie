import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from config import CONFIG
from functions.shortcut_utils import open_start_menu, open_action_center, open_explorer_window, open_onscreen_keyboard


class InvisibleUI(QWidget):
    """A clock with no seconds and a 50% transparent background."""

    def __init__(self, obj_name: str = "InvisibleUI", parent=None, button_size: int = 5):
        super().__init__(parent)
        self.obj_name = obj_name
        self.setWindowTitle(f"{CONFIG.PROGRAM_NAME} - InvisibleUI")  # Set the window title
        self.button_size = button_size  # Button size variable

        # Set up window properties
        self.setup_window()

        # Create buttons
        # self.btn_btm_left = QPushButton("", self)
        # self.btn_btm_left.setObjectName("InvisibleButton")
        # self.btn_btm_right = QPushButton("", self)
        # self.btn_btm_right.setObjectName("InvisibleButton")
        # self.btn_btm_center = QPushButton("", self)
        # self.btn_btm_center.setObjectName("InvisibleButton")
        self.btn_ctr_left = QPushButton("", self)
        self.btn_ctr_left.setObjectName("InvisibleButton")

        # Set button sizes
        # self.btn_btm_left.setFixedSize(90, self.button_size)
        # self.btn_btm_right.setFixedSize(90, self.button_size)
        # self.btn_btm_center.setFixedSize(1000, self.button_size)
        self.btn_ctr_left.setFixedSize(self.button_size, 600)

        # Connect buttons to print functions
        # self.btn_btm_left.clicked.connect(lambda: open_start_menu(self, hide_parent=False))
        # self.btn_btm_right.clicked.connect(lambda: open_action_center(self, hide_parent=False))
        # self.btn_btm_center.clicked.connect(lambda: open_onscreen_keyboard(self, hide_parent=False))
        self.btn_ctr_left.clicked.connect(lambda: open_explorer_window(self, hide_parent=False))

        # Initial position of buttons
        self.position_buttons()

    def setup_window(self):
        """Set up the main window properties."""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Keep window background transparent
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)

        # Resize the window to half screen width (half of the screen width, full screen height)
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height())  # Full height, half width

    def resizeEvent(self, event):
        """Reposition buttons when the window is resized."""
        super().resizeEvent(event)
        self.position_buttons()

    def position_buttons(self):
        """Position the buttons at the bottom-left and bottom-right corners."""
        # Move buttons to the bottom-left and bottom-right corners
        # self.btn_btm_left.move(0, self.height() - self.btn_btm_left.height())  # Align with the bottom-left corner
        # self.btn_btm_right.move(self.width() - self.btn_btm_right.width(),
        #                         self.height() - self.btn_btm_right.height())  # Align with the bottom-right corner
        # self.btn_btm_center.move(self.width() // 2 - self.btn_btm_center.width() // 2,
        #                          self.height() - self.btn_btm_center.height())  # Align with the bottom center
        self.btn_ctr_left.move(0, self.height() // 2 - self.btn_ctr_left.height() // 2)  # Align with the center left edge

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
