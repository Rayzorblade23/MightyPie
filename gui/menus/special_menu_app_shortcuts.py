import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QApplication

from gui.menus.button_info_editor import ButtonInfoEditor
from data.config import CONFIG
from gui.menus.config_settings_menu import ConfigSettingsWindow
from functions.icon_utils import get_icon
from functions.window_functions import clear_cache


class AppSettingsMenu(QWidget):
    # noinspection PyUnresolvedReferences
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up the window
        self.setWindowTitle('Settings Menu')
        self.setGeometry(100, 100, 600, 100)  # Increased width for HBoxLayout

        self.icon_size = (20, 20)
        self.inverted_icons = True

        self.button_config = ButtonInfoEditor()

        self.app_settings = ConfigSettingsWindow()

        if CONFIG.SHOW_SETTINGS_AT_STARTUP:
            self.app_settings.show()

        def create_button(parent, icon_name, tooltip, click_action, icon_size, button_height):
            button = QPushButton(parent)
            button.setIcon(get_icon(icon_name, is_inverted=True))
            button.setIconSize(QSize(*icon_size))
            button.setFixedSize(button_height, button_height)
            button.setToolTip(tooltip)
            button.clicked.connect(click_action)
            return button

        default_spacing = 6
        spacer = QSpacerItem(CONFIG.INTERNAL_BUTTON_HEIGHT + default_spacing, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # Define buttons and their properties
        # (icon_name, tooltip, click_action)
        buttons_data = [
            ("shredder", "Clear App Info Cache", lambda: clear_cache(self)),
            ("cake", "Open the Button Config", lambda: self.open_button_info_editor()),
            ("settings", "Open the App Settings", lambda: self.open_settings_window()),
            ("restart", "Restart Program", lambda: self.parent().main_window.restart_program()),
            ("quit", "Quit Program", lambda: self.parent().main_window.quit_program()),
        ]

        # Create and store buttons
        buttons = [
            create_button(self, icon_name, tooltip, click_action, self.icon_size, CONFIG.INTERNAL_BUTTON_HEIGHT)
            for icon_name, tooltip, click_action in buttons_data
        ]

        # Set up the horizontal layout
        layout = QHBoxLayout()
        layout.setSpacing(default_spacing)

        # Add buttons to layout
        for button in buttons[:1]:  # Add the first set of buttons
            layout.addWidget(button)

        layout.addSpacerItem(spacer)

        for button in buttons[1:]:  # Add the middle set of buttons
            layout.addWidget(button)

        # Remove spacing between buttons and margins around layout
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align buttons to the left

        # Set the layout for the window
        self.setLayout(layout)

    def open_button_info_editor(self):
        if self.button_config is None:
            self.button_config = ButtonInfoEditor()
        self.button_config.show()

    def open_settings_window(self):
        if self.app_settings is None:
            self.app_settings = ConfigSettingsWindow()
        self.app_settings.show()


# Main entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AppSettingsMenu()
    window.show()
    sys.exit(app.exec())
