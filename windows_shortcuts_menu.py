import os
import os
import sys

from PyQt6.QtCore import QSize, Qt, QCoreApplication
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QApplication

from GUI.icon_functions_and_paths import get_icon
from button_info_editor import ButtonInfoEditor
from config import CONFIG
from functions.shortcut_utils import open_audio_settings, open_network_settings, open_projection_settings, \
    open_explorer_window, open_task_manager
from functions.window_functions import clear_cache


class WindowsSettingsMenu(QWidget):
    # noinspection PyUnresolvedReferences
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up the window
        self.setWindowTitle('Settings Menu')
        self.setGeometry(100, 100, 600, 100)  # Increased width for HBoxLayout

        self.icon_size = (20, 20)
        self.inverted_icons = True

        self.button_config = None

        def create_button(parent, icon_name, tooltip, click_action, icon_size, button_height):
            button = QPushButton(parent)
            button.setIcon(get_icon(icon_name, is_inverted=True))
            button.setIconSize(QSize(*icon_size))
            button.setFixedSize(button_height, button_height)
            button.setToolTip(tooltip)
            button.clicked.connect(click_action)
            return button

        default_spacing = 6
        spacer = QSpacerItem(CONFIG.BUTTON_HEIGHT + default_spacing, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # Define buttons and their properties
        # (icon_name, tooltip, click_action)
        buttons_data = [
            ("taskman", "Open Task Manager", lambda: open_task_manager(self, hide_parent=True)),
            ("audio", "Open Audio Settings", lambda: open_audio_settings(self, hide_parent=True)),
            ("network", "Open Network Settings", lambda: open_network_settings(self, hide_parent=True)),
            ("projection", "Open Projection Settings", lambda: open_projection_settings(self, hide_parent=True)),
            ("folder", "Open File Explorer", lambda: open_explorer_window(self, hide_parent=True)),
            ("shredder", "Clear App Info Cache", lambda: clear_cache()),
            ("restart", "Restart Program", lambda: restart_program()),
            ("quit", "Quit Program", lambda: quit_program()),
            ("settings", "Open the Button Config", lambda: self.open_button_info_editor()),
        ]

        # Create and store buttons
        buttons = [
            create_button(self, icon_name, tooltip, click_action, self.icon_size, CONFIG.BUTTON_HEIGHT)
            for icon_name, tooltip, click_action in buttons_data
        ]

        # Set up the horizontal layout
        layout = QHBoxLayout()
        layout.setSpacing(default_spacing)

        # Add buttons to layout
        for button in buttons[:4]:  # Add the first set of buttons
            layout.addWidget(button)

        layout.addSpacerItem(spacer)

        for button in buttons[4:6]:  # Add the middle set of buttons
            layout.addWidget(button)

        layout.addSpacerItem(spacer)

        for button in buttons[6:]:  # Add the last set of buttons
            layout.addWidget(button)

        # Remove spacing between buttons and margins around layout
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align buttons to the left

        # Set the layout for the window
        self.setLayout(layout)

    def open_button_info_editor(self):
        if self.button_config is None:
            self.button_config = ButtonInfoEditor()
        self.button_config.show()


def restart_program():
    """Restart the current program."""
    print("Restarting program...")  # Debugging output

    # Quit the application
    QCoreApplication.quit()

    # Re-launch the program as an external process
    python = sys.executable
    os.spawnl(os.P_NOWAIT, python, python, *sys.argv)
    sys.exit()


def quit_program():
    QCoreApplication.exit()


# Main entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WindowsSettingsMenu()
    window.show()
    sys.exit(app.exec())
