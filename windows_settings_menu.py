import sys
import subprocess
import pyautogui
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout

from config import CONFIG


class WindowsSettingsMenu(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle('Settings Menu')
        self.setGeometry(100, 100, 600, 100)  # Increased width for HBoxLayout

        # Create buttons with updated names
        self.audio_button = QPushButton('Audio Settings', self)
        self.audio_button.clicked.connect(self.open_audio_settings)
        self.audio_button.setFixedHeight(CONFIG.BUTTON_HEIGHT)

        self.network_button = QPushButton('Network Settings', self)
        self.network_button.clicked.connect(self.open_network_settings)
        self.network_button.setFixedHeight(CONFIG.BUTTON_HEIGHT)

        self.action_center_button = QPushButton('Action Center', self)
        self.action_center_button.clicked.connect(self.open_action_center)
        self.action_center_button.setFixedHeight(CONFIG.BUTTON_HEIGHT)

        self.projection_button = QPushButton('Switch Monitors', self)  # Updated button text
        self.projection_button.clicked.connect(self.open_projection_settings)
        self.projection_button.setFixedHeight(CONFIG.BUTTON_HEIGHT)

        # Set up the horizontal layout
        layout = QHBoxLayout()
        layout.addWidget(self.audio_button)
        layout.addWidget(self.network_button)
        layout.addWidget(self.action_center_button)
        layout.addWidget(self.projection_button)

        # Set the layout for the window
        self.setLayout(layout)

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


# Main entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WindowsSettingsMenu()
    window.show()
    sys.exit(app.exec())
