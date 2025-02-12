import sys

import pyautogui
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QApplication

from data.config import CONFIG
from functions.icon_utils import get_icon


class MonitorSetupMenu(QWidget):
    # noinspection PyUnresolvedReferences
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up the window
        self.setWindowTitle('Monitor Settings Menu')
        self.setGeometry(100, 100, 600, 100)  # Increased width for HBoxLayout

        self.icon_size = (20, 20)
        self.inverted_icons = True

        self.button_config = None

        def create_button(parent, icon_name, tooltip, click_action, icon_size, button_height, text=""):
            button = QPushButton(text, parent)
            if icon_name:
                button.setIcon(get_icon(icon_name, is_inverted=True))
            button.setIconSize(QSize(*icon_size))
            button.setFixedHeight(button_height)
            if tooltip:
                button.setToolTip(tooltip)
            button.clicked.connect(click_action)
            return button

        default_spacing = 6

        # Define buttons and their properties
        # (icon_name, tooltip, click_action)
        buttons_data = [
            ("", "", lambda: pyautogui.hotkey(*CONFIG.MONITOR_SHORTCUT_1), "Desk Single"),
            ("", "", lambda: pyautogui.hotkey(*CONFIG.MONITOR_SHORTCUT_2), "Desk Dual"),
            ("", "", lambda: (pyautogui.hotkey(*CONFIG.MONITOR_SHORTCUT_3)), "TV"),
        ]

        # Create and store buttons
        buttons = [
            create_button(self, icon_name, tooltip, click_action, self.icon_size, CONFIG.INTERNAL_BUTTON_HEIGHT, text)
            for icon_name, tooltip, click_action, text in buttons_data
        ]

        # Set up the horizontal layout
        layout = QHBoxLayout()
        layout.setSpacing(default_spacing)

        # Add buttons to layout
        for button in buttons:
            layout.addWidget(button)

        # Remove spacing between buttons and margins around layout
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align buttons to the left

        # Set the layout for the window
        self.setLayout(layout)


# Main entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MonitorSetupMenu()
    window.show()
    sys.exit(app.exec())
