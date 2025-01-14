import os
import sys

from PyQt6.QtCore import QSize, Qt, QCoreApplication
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QApplication

from GUI.icon_functions_and_paths import get_icon
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

        # # Create a button to press the Windows key (using icon)
        # self.windows_key_button = QPushButton(self)
        # self.windows_key_button.setIcon(get_icon("windows_key", is_inverted=True))
        # self.windows_key_button.setIconSize(QSize(*self.icon_size))
        # self.windows_key_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        # self.windows_key_button.clicked.connect(lambda: open_start_menu(self, hide_parent=True))

        # Create other buttons with icons
        self.audio_button = QPushButton(self)
        self.audio_button.setIcon(get_icon("audio", is_inverted=True))
        self.audio_button.setIconSize(QSize(*self.icon_size))
        self.audio_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.audio_button.clicked.connect(lambda: open_audio_settings(self, hide_parent=True))

        self.network_button = QPushButton(self)
        self.network_button.setIcon(get_icon("network", is_inverted=True))
        self.network_button.setIconSize(QSize(*self.icon_size))
        self.network_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.network_button.clicked.connect(lambda: open_network_settings(self, hide_parent=True))

        # self.action_center_button = QPushButton(self)
        # self.action_center_button.setIcon(get_icon("action_center", is_inverted=True))
        # self.action_center_button.setIconSize(QSize(*self.icon_size))
        # self.action_center_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        # self.action_center_button.clicked.connect(lambda: open_action_center(self, hide_parent=True))

        self.projection_button = QPushButton(self)
        self.projection_button.setIcon(get_icon("projection", is_inverted=True))
        self.projection_button.setIconSize(QSize(*self.icon_size))
        self.projection_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.projection_button.clicked.connect(lambda: open_projection_settings(self, hide_parent=True))

        # self.touch_keyboard_button = QPushButton(self)
        # self.touch_keyboard_button.setIcon(get_icon("touch_keyboard", is_inverted=True))
        # self.touch_keyboard_button.setIconSize(QSize(*self.icon_size))
        # self.touch_keyboard_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        # self.touch_keyboard_button.clicked.connect(lambda: open_onscreen_keyboard(self, hide_parent=True))

        self.explorer_button = QPushButton(self)
        self.explorer_button.setIcon(get_icon("folder", is_inverted=True))
        self.explorer_button.setIconSize(QSize(*self.icon_size))
        self.explorer_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.explorer_button.clicked.connect(lambda: open_explorer_window(self, hide_parent=True))

        self.task_man_button = QPushButton(self)
        self.task_man_button.setIcon(get_icon("taskman", is_inverted=True))
        self.task_man_button.setIconSize(QSize(*self.icon_size))
        self.task_man_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.task_man_button.clicked.connect(lambda: open_task_manager(self, hide_parent=True))

        self.restart_button = QPushButton(self)
        self.restart_button.setIcon(get_icon("restart", is_inverted=True))
        self.restart_button.setIconSize(QSize(*self.icon_size))
        self.restart_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.restart_button.clicked.connect(lambda: self.restart_program())

        self.quit_button = QPushButton(self)
        self.quit_button.setIcon(get_icon("quit", is_inverted=True))
        self.quit_button.setIconSize(QSize(*self.icon_size))
        self.quit_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.quit_button.clicked.connect(lambda: self.quit_program())

        self.clear_cache_button = QPushButton(self)
        self.clear_cache_button.setIcon(get_icon("shredder", is_inverted=True))
        self.clear_cache_button.setIconSize(QSize(*self.icon_size))
        self.clear_cache_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.clear_cache_button.clicked.connect(lambda: clear_cache())

        default_spacing = 6
        spacer = QSpacerItem(CONFIG.BUTTON_HEIGHT + default_spacing, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # Add tooltips for buttons
        self.audio_button.setToolTip("Open Audio Settings")
        self.network_button.setToolTip("Open Network Settings")
        self.projection_button.setToolTip("Open Projection Settings")
        self.explorer_button.setToolTip("Open File Explorer")
        self.task_man_button.setToolTip("Open Task Manager")
        self.clear_cache_button.setToolTip("Clear App Info Cache")

        # self.windows_key_button.setToolTip("Open Start Menu")
        # self.touch_keyboard_button.setToolTip("Open On-Screen Keyboard")
        # self.action_center_button.setToolTip("Open Action Center")
        # layout.addWidget(self.windows_key_button)  # Add the Windows key button first
        # layout.addWidget(self.touch_keyboard_button)
        # layout.addWidget(self.action_center_button)

        # Set up the horizontal layout
        layout = QHBoxLayout()
        layout.setSpacing(default_spacing)

        layout.addWidget(self.task_man_button)
        layout.addWidget(self.audio_button)
        layout.addWidget(self.network_button)
        layout.addWidget(self.projection_button)

        layout.addSpacerItem(spacer)
        layout.addWidget(self.explorer_button)
        layout.addWidget(self.clear_cache_button)

        layout.addSpacerItem(spacer)

        layout.addWidget(self.restart_button)
        layout.addWidget(self.quit_button)

        # Remove spacing between buttons and margins around layout
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align buttons to the left

        # Set the layout for the window
        self.setLayout(layout)

    def restart_program(self):
        """Restart the current program."""
        print("Restarting program...")  # Debugging output

        # Quit the application
        QCoreApplication.quit()

        # Re-launch the program as an external process
        python = sys.executable
        os.spawnl(os.P_NOWAIT, python, python, *sys.argv)
        sys.exit()

    def quit_program(self):
        # Process any remaining events
        print("WHY")
        QCoreApplication.exit()


# Main entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WindowsSettingsMenu()
    window.show()
    sys.exit(app.exec())
