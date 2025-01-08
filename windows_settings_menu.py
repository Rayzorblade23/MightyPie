import os
import subprocess
import sys

import pyautogui
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout

from config import CONFIG


class WindowsSettingsMenu(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle('Settings Menu')
        self.setGeometry(100, 100, 600, 100)  # Increased width for HBoxLayout

        self.icon_size = (20,20)
        self.inverted_icons = True

        # Define the icon file paths (use appropriate file paths)
        icon_paths = {
            "windows_key": os.path.join("external_icons", "brand-windows.png"),
            "audio": os.path.join("external_icons", "volume.png"),
            "network": os.path.join("external_icons", "network.png"),
            "action_center": os.path.join("external_icons", "layout-sidebar-right-inactive.png"),
            "projection": os.path.join("external_icons", "device-desktop.png"),
            "touch_keyboard": os.path.join("external_icons", "keyboard.png")
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
        self.windows_key_button.clicked.connect(self.press_windows_key)

        # Create other buttons with icons
        self.audio_button = QPushButton(self)
        self.audio_button.setIcon(get_icon("audio"))
        self.audio_button.setIconSize(QSize(*self.icon_size))
        self.audio_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.audio_button.clicked.connect(self.open_audio_settings)

        self.network_button = QPushButton(self)
        self.network_button.setIcon(get_icon("network"))
        self.network_button.setIconSize(QSize(*self.icon_size))
        self.network_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.network_button.clicked.connect(self.open_network_settings)

        self.action_center_button = QPushButton(self)
        self.action_center_button.setIcon(get_icon("action_center"))
        self.action_center_button.setIconSize(QSize(*self.icon_size))
        self.action_center_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.action_center_button.clicked.connect(self.open_action_center)

        self.projection_button = QPushButton(self)
        self.projection_button.setIcon(get_icon("projection"))
        self.projection_button.setIconSize(QSize(*self.icon_size))
        self.projection_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.projection_button.clicked.connect(self.open_projection_settings)

        self.touch_keyboard_button = QPushButton(self)
        self.touch_keyboard_button.setIcon(get_icon("touch_keyboard"))
        self.touch_keyboard_button.setIconSize(QSize(*self.icon_size))
        self.touch_keyboard_button.setFixedSize(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)  # Set button size
        self.touch_keyboard_button.clicked.connect(self.open_touch_keyboard)

        # Set up the horizontal layout
        layout = QHBoxLayout()
        layout.addWidget(self.windows_key_button)  # Add the Windows key button first
        layout.addWidget(self.audio_button)
        layout.addWidget(self.network_button)
        layout.addWidget(self.action_center_button)
        layout.addWidget(self.projection_button)
        layout.addWidget(self.touch_keyboard_button)

        # Remove spacing between buttons and margins around layout
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align buttons to the left

        # Set the layout for the window
        self.setLayout(layout)

    def press_windows_key(self):
        """Simulate pressing Ctrl + Esc to open the Start menu"""
        try:
            # Simulate pressing Ctrl + Esc
            pyautogui.hotkey('ctrl', 'esc')
            self.parent().hide()  # Hide the parent window after the button is pressed
        except Exception as e:
            print(f"Error pressing Ctrl + Esc: {e}")

    def open_audio_settings(self):
        """Open the Windows 10 audio settings"""
        try:
            subprocess.run(["explorer", "ms-settings:sound"], check=False)
            self.parent().hide()  # Hide the parent window after the button is pressed
        except FileNotFoundError:
            print("Error: Explorer or ms-settings:sound command not found.")
        except subprocess.CalledProcessError as e:
            print(f"Error opening audio settings: {e}")

    def open_network_settings(self):
        """Open the Windows 10 network settings"""
        try:
            subprocess.run(["explorer", "ms-settings:network-status"], check=False)
            self.parent().hide()  # Hide the parent window after the button is pressed
        except FileNotFoundError:
            print("Error: Explorer or ms-settings:network-status command not found.")
        except subprocess.CalledProcessError as e:
            print(f"Error opening network settings: {e}")

    def open_action_center(self):
        """Open the Windows 10 Action Center"""
        try:
            pyautogui.hotkey('win', 'a')  # Simulate pressing Win + A
            self.parent().hide()  # Hide the parent window after the button is pressed
        except Exception as e:
            print(f"Error opening Action Center: {e}")

    def open_projection_settings(self):
        """Open the Windows 10 projection settings (Win + P)"""
        try:
            pyautogui.hotkey('win', 'p')  # Simulate pressing Win + P
            self.parent().hide()  # Hide the parent window after the button is pressed
        except Exception as e:
            print(f"Error opening projection settings: {e}")

    def open_touch_keyboard(self):
        """Open the Windows On-Screen Touch Keyboard"""
        try:
            subprocess.run("osk.exe")  # Launch the On-Screen Keyboard
            self.parent().hide()  # Hide the parent window after the button is pressed
        except Exception as e:
            print(f"Error opening touch keyboard: {e}")

    def invert_icon(self,icon_path):
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
