import os
import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy

from config import CONFIG
from functions.shortcut_utils import open_audio_settings, open_network_settings, open_action_center, open_projection_settings, \
    open_onscreen_keyboard, open_start_menu, open_explorer_window, open_task_manager


class WindowsSettingsMenu(QWidget):
    # noinspection PyUnresolvedReferences
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle('Settings Menu')
        self.setGeometry(100, 100, 600, 100)  # Increased width for HBoxLayout

        self.icon_size = (20, 20)
        self.inverted_icons = True

        # Define the icon file paths (use appropriate file paths)
        icon_paths = {
            "windows_key": os.path.join("external_icons", "brand-windows.png"),
            "audio": os.path.join("external_icons", "volume.png"),
            "network": os.path.join("external_icons", "network.png"),
            "action_center": os.path.join("external_icons", "layout-sidebar-right-inactive.png"),
            "projection": os.path.join("external_icons", "device-desktop.png"),
            "touch_keyboard": os.path.join("external_icons", "keyboard.png"),
            "folder": os.path.join("external_icons", "folder.png"),
            "taskman": os.path.join("external_icons", "subtask.png")
        }

        # Load the icon based on the inverted_icons flag
        def get_icon(icon_name):
            icon_path = icon_paths.get(icon_name)

            if icon_path:
                if self.inverted_icons:
                    return self.invert_icon(icon_path)  # Return inverted icon
                else:
                    return QIcon(icon_path)  # Return original icon
            return None  # In case icon name doesn't match

        # Create a button to press the Windows key (using icon)
        self.windows_key_button = QPushButton(self)
        self.windows_key_button.setIcon(get_icon("windows_key"))
        self.windows_key_button.setIconSize(QSize(*self.icon_size))
        self.windows_key_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.windows_key_button.clicked.connect(lambda: open_start_menu(self, hide_parent=True))

        # Create other buttons with icons
        self.audio_button = QPushButton(self)
        self.audio_button.setIcon(get_icon("audio"))
        self.audio_button.setIconSize(QSize(*self.icon_size))
        self.audio_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.audio_button.clicked.connect(lambda: open_audio_settings(self, hide_parent=True))

        self.network_button = QPushButton(self)
        self.network_button.setIcon(get_icon("network"))
        self.network_button.setIconSize(QSize(*self.icon_size))
        self.network_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.network_button.clicked.connect(lambda: open_network_settings(self, hide_parent=True))

        self.action_center_button = QPushButton(self)
        self.action_center_button.setIcon(get_icon("action_center"))
        self.action_center_button.setIconSize(QSize(*self.icon_size))
        self.action_center_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.action_center_button.clicked.connect(lambda: open_action_center(self, hide_parent=True))

        self.projection_button = QPushButton(self)
        self.projection_button.setIcon(get_icon("projection"))
        self.projection_button.setIconSize(QSize(*self.icon_size))
        self.projection_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.projection_button.clicked.connect(lambda: open_projection_settings(self, hide_parent=True))

        self.touch_keyboard_button = QPushButton(self)
        self.touch_keyboard_button.setIcon(get_icon("touch_keyboard"))
        self.touch_keyboard_button.setIconSize(QSize(*self.icon_size))
        self.touch_keyboard_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.touch_keyboard_button.clicked.connect(lambda: open_onscreen_keyboard(self, hide_parent=True))

        self.explorer_button = QPushButton(self)
        self.explorer_button.setIcon(get_icon("folder"))
        self.explorer_button.setIconSize(QSize(*self.icon_size))
        self.explorer_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.explorer_button.clicked.connect(lambda: open_explorer_window(self, hide_parent=True))

        self.task_man_button = QPushButton(self)
        self.task_man_button.setIcon(get_icon("taskman"))
        self.task_man_button.setIconSize(QSize(*self.icon_size))
        self.task_man_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.task_man_button.clicked.connect(lambda: open_task_manager(self, hide_parent=True))

        default_spacing = 6
        spacer = QSpacerItem(CONFIG.BUTTON_HEIGHT + default_spacing, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # Add tooltips for buttons
        self.windows_key_button.setToolTip("Open Start Menu")
        self.audio_button.setToolTip("Open Audio Settings")
        self.network_button.setToolTip("Open Network Settings")
        self.action_center_button.setToolTip("Open Action Center")
        self.projection_button.setToolTip("Open Projection Settings")
        self.touch_keyboard_button.setToolTip("Open On-Screen Keyboard")
        self.explorer_button.setToolTip("Open File Explorer")
        self.task_man_button.setToolTip("Open Task Manager")

        # Set up the horizontal layout
        layout = QHBoxLayout()
        layout.setSpacing(default_spacing)

        layout.addWidget(self.task_man_button)
        layout.addWidget(self.audio_button)
        layout.addWidget(self.network_button)
        layout.addWidget(self.projection_button)

        layout.addSpacerItem(spacer)

        layout.addWidget(self.windows_key_button)  # Add the Windows key button first
        layout.addWidget(self.touch_keyboard_button)
        layout.addWidget(self.explorer_button)
        layout.addWidget(self.action_center_button)

        # Remove spacing between buttons and margins around layout
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align buttons to the left

        # Set the layout for the window
        self.setLayout(layout)

    def invert_icon(self, icon_path):
        """Invert the colors of the icon, preserving the alpha channel."""
        # Load the icon as QPixmap
        pixmap = QPixmap(icon_path)

        # Convert QPixmap to QImage for manipulation
        image = pixmap.toImage()

        # Loop through each pixel and invert its color (keep alpha intact)
        for x in range(image.width()):
            for y in range(image.height()):
                color = image.pixelColor(x, y)

                # Skip pixels with full transparency (alpha = 0)
                if color.alpha() == 0:
                    continue

                # Invert RGB, but keep the alpha channel intact
                inverted_color = QColor(255 - color.red(), 255 - color.green(), 255 - color.blue(), color.alpha())
                image.setPixelColor(x, y, inverted_color)

        # Convert the QImage back to QPixmap and return it as a QIcon
        inverted_pixmap = QPixmap.fromImage(image)
        return QIcon(inverted_pixmap)


# Main entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WindowsSettingsMenu()
    window.show()
    sys.exit(app.exec())
