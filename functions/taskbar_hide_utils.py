import atexit
import ctypes
import subprocess
import sys
import time

import win32con
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget


class TaskbarController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_hidden = False

        # if not self.is_admin():
        #     self.elevate_to_admin()

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Taskbar Control")
        self.setGeometry(100, 100, 200, 50)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.toggle_button = QPushButton("Hide Taskbar", self)
        self.toggle_button.clicked.connect(self.toggle_taskbar)
        layout.addWidget(self.toggle_button)

    def closeEvent(self, event):
        if self.is_hidden:
            show_taskbar()
        event.accept()

    def toggle_taskbar(self):
        if not self.is_hidden:
            hide_taskbar()
            self.toggle_button.setText("Show Taskbar")
        else:
            show_taskbar()
            self.toggle_button.setText("Hide Taskbar")
        self.is_hidden = not self.is_hidden


def set_taskbar_opacity(alpha_value: int):
    """Set the opacity of the taskbar with an integer value (0 to 255)."""
    hwnd = get_taskbar_handle()

    if hwnd == 0:
        print("Failed to get taskbar handle!")
        return

    # Constants
    GWL_EXSTYLE = -20  # Index for extended window styles
    WS_EX_LAYERED = 0x00080000  # Layered window style
    LWA_ALPHA = 0x00000002  # Layered Window Attribute for alpha transparency

    # Clamp alpha_value to the range [0, 255]
    alpha_value = max(0, min(255, alpha_value))

    # Add the WS_EX_LAYERED style to the taskbar window
    current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if not (current_style & WS_EX_LAYERED):
        new_style = current_style | WS_EX_LAYERED
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

    # Apply the alpha transparency
    result = ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, alpha_value, LWA_ALPHA)

    if result == 0:
        print("Failed to apply transparency!")
    else:
        print("Transparency applied successfully.")


# def toggle_taskbar_autohide(state):
#     reg_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3"
#     try:
#         reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0,
#                                  winreg.KEY_SET_VALUE | winreg.KEY_READ)
#         settings_value, _ = winreg.QueryValueEx(reg_key, "Settings")
#         settings_value = bytearray(settings_value)
#         settings_value[8] = 0x03 if state else 0x02
#         winreg.SetValueEx(reg_key, "Settings", 0, winreg.REG_BINARY, bytes(settings_value))
#         restart_explorer()
#         time.sleep(5)
#     finally:
#         winreg.CloseKey(reg_key)


def restart_explorer():
    subprocess.run("taskkill /f /im explorer.exe", shell=True)
    subprocess.run("start explorer.exe", shell=True)


def get_taskbar_handle():
    hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
    attempts = 5
    while hwnd == 0 and attempts > 0:
        time.sleep(1)
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        attempts -= 1
    return hwnd


# Function to get the taskbar's rectangle (position and size)
def get_taskbar_rect():
    hwnd = get_taskbar_handle()
    if hwnd == 0:
        return None  # Taskbar not found

    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect


def hide_taskbar():
    hwnd = get_taskbar_handle()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_HIDE)
    else:
        print("Failed to retrieve taskbar handle.")


def show_taskbar():
    hwnd = get_taskbar_handle()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_SHOW)
    else:
        print("Failed to retrieve taskbar handle.")

    # def is_admin(self):
    #     try:
    #         return ctypes.windll.shell32.IsUserAnAdmin() != 0
    #     except:
    #         return False
    #
    # def elevate_to_admin(self):
    #     script = sys.argv[0]
    #     params = ' '.join(sys.argv[1:])
    #     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    #     sys.exit(0)


# Ensure taskbar is shown when the program exits
atexit.register(show_taskbar)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TaskbarController()
    window.show()
    sys.exit(app.exec())
