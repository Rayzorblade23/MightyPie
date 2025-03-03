from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy

from src.data.config import CONFIG
from src.utils.icon_utils import get_icon
from src.utils.shortcut_utils import open_audio_settings, open_network_settings, open_projection_settings, \
    open_explorer_window, open_task_manager


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
        spacer = QSpacerItem(CONFIG.INTERNAL_BUTTON_HEIGHT + default_spacing, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # Define buttons and their properties
        # (icon_name, tooltip, click_action)
        buttons_data = [
            ("taskman", "Open Task Manager", lambda: open_task_manager(self, hide_parent=True)),
            ("audio", "Open Audio Settings", lambda: open_audio_settings(self, hide_parent=True)),
            ("network", "Open Network Settings", lambda: open_network_settings(self, hide_parent=True)),
            ("projection", "Open Projection Settings", lambda: open_projection_settings(self, hide_parent=True)),
            ("folder", "Open File Explorer", lambda: open_explorer_window(self, hide_parent=True)),
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
        for button in buttons:
            layout.addWidget(button)

        # Remove spacing between buttons and margins around layout
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align buttons to the left

        # Set the layout for the window
        self.setLayout(layout)
