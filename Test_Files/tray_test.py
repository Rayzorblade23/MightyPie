from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout
from pywinauto import Desktop, Application
import logging
import sys
import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes, Structure, Union, sizeof, POINTER, cast, c_void_p

# Define HRESULT as a signed long
wintypes.HRESULT = ctypes.c_long

# Shell_NotifyIcon messages
NIM_SETVERSION = 0x00000004
NOTIFYICON_VERSION = 3
NOTIFYICON_VERSION_4 = 4
NIM_SETFOCUS = 0x00000003

# Custom messages
WM_SHELLNOTIFY = win32con.WM_USER + 1

class POINT(Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class GUID(Structure):
    _fields_ = [
        ("Data1", wintypes.ULONG),
        ("Data2", wintypes.USHORT),
        ("Data3", wintypes.USHORT),
        ("Data4", wintypes.BYTE * 8)
    ]

class NOTIFYICONIDENTIFIER(Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("guidItem", GUID),
    ]

# Load Shell32.dll functions
shell32 = ctypes.WinDLL('shell32.dll')
Shell_NotifyIconGetRect = shell32.Shell_NotifyIconGetRect
Shell_NotifyIconGetRect.argtypes = [POINTER(NOTIFYICONIDENTIFIER), POINTER(wintypes.RECT)]
Shell_NotifyIconGetRect.restype = wintypes.HRESULT

# Remaining code...



class SystemTrayInspector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.level4_elements = []
        self.notify_icons = []
        self.setup_logging()
        self.init_ui()
        self.gather_tray_elements()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def init_ui(self):
        self.setWindowTitle('System Tray Inspector')
        self.resize(400, 300)
        central_widget = QWidget()
        self.layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

    def find_tray_window(self):
        """Find the system tray window."""
        try:
            shell_tray = win32gui.FindWindow('Shell_TrayWnd', None)
            tray_notify = win32gui.FindWindowEx(shell_tray, 0, 'TrayNotifyWnd', None)
            return tray_notify
        except Exception as e:
            self.logger.error(f"Error finding tray window: {e}")
            return None

    def gather_tray_elements(self):
        """Gather both regular and NotifyIcon elements."""
        try:
            # Get regular tray elements
            tray_hwnd = self.find_tray_window()
            if tray_hwnd:
                desktop = Desktop(backend='uia')
                tray = desktop.window(handle=tray_hwnd)
                self._gather_elements_from_tray(tray)

            # Get NotifyIcon elements
            self._gather_notify_icons(tray_hwnd)

            # Create buttons for all found elements
            self._create_element_buttons()

        except Exception as e:
            self.logger.error(f"Error gathering tray elements: {e}")

    def _gather_notify_icons(self, tray_hwnd):
        """Gather NotifyIcon elements using Shell_NotifyIcon API."""
        try:
            # Enumerate windows to find notify icon windows
            def enum_windows_callback(hwnd, ctx):
                class_name = win32gui.GetClassName(hwnd)
                if class_name == "NotifyIconOverflowWindow":
                    self._process_notify_window(hwnd)
                return True

            win32gui.EnumWindows(enum_windows_callback, None)

        except Exception as e:
            self.logger.error(f"Error gathering notify icons: {e}")

    def _process_notify_window(self, hwnd):
        """Process a notify icon window to extract icon information."""
        try:
            # Get window information
            rect = win32gui.GetWindowRect(hwnd)
            title = win32gui.GetWindowText(hwnd)

            # Create a NotifyIcon element representation
            notify_icon = {
                'hwnd': hwnd,
                'title': title,
                'rect': rect,
                'type': 'notify_icon'
            }

            self.notify_icons.append(notify_icon)
            self.logger.info(f"Found notify icon: {title}")

        except Exception as e:
            self.logger.error(f"Error processing notify window: {e}")

    def _gather_elements_from_tray(self, tray_window):
        """Gather regular tray elements."""
        try:
            buttons = tray_window.descendants(control_type="Button")
            for button in buttons:
                self.level4_elements.append(button)
                self.logger.info(f"Found tray element: {button.window_text()}")

        except Exception as e:
            self.logger.error(f"Error gathering elements from tray: {e}")

    def _create_element_buttons(self):
        """Create buttons for all found elements."""
        # Create buttons for regular elements
        for element in self.level4_elements:
            self._create_element_button_pair(
                text=element.window_text() or "[No Text]",
                on_info=lambda e=element: self.show_element_info(e),
                on_context=lambda e=element: self.open_context_menu(e)
            )

        # Create buttons for notify icons
        for icon in self.notify_icons:
            self._create_element_button_pair(
                text=icon['title'] or "[No Title]",
                on_info=lambda i=icon: self.show_notify_icon_info(i),
                on_context=lambda i=icon: self.open_notify_icon_menu(i)
            )

    def _create_element_button_pair(self, text, on_info, on_context):
        """Create a pair of buttons (Info and Context Menu) for an element."""
        try:
            h_layout = QHBoxLayout()

            # Info button
            info_btn = QPushButton(text)
            info_btn.clicked.connect(on_info)
            h_layout.addWidget(info_btn)

            # Context menu button
            context_btn = QPushButton("Context Menu")
            context_btn.clicked.connect(on_context)
            h_layout.addWidget(context_btn)

            self.layout.addLayout(h_layout)

        except Exception as e:
            self.logger.error(f"Error creating button pair: {e}")

    def show_element_info(self, element):
        """Show information about a regular tray element."""
        try:
            rect = element.rectangle()
            self.logger.info(
                f'Element: {element.window_text()}\n'
                f'Handle: {element.handle}\n'
                f'Class Name: {element.class_name()}\n'
                f'Position: Left={rect.left}, Top={rect.top}, '
                f'Right={rect.right}, Bottom={rect.bottom}'
            )

            control_type = getattr(element.element_info, 'control_type', 'Unknown')
            automation_id = getattr(element.element_info, 'automation_id', None) or 'None'
            runtime_id = getattr(element.element_info, 'runtime_id', None) or 'None'

            self.logger.info(
                f'Control Type: {control_type}\n'
                f'Automation ID: {automation_id}\n'
                f'Runtime ID: {runtime_id}'
            )

        except Exception as e:
            self.logger.error(f"Error showing element info: {e}")

    def show_notify_icon_info(self, icon):
        """Show information about a NotifyIcon element."""
        try:
            self.logger.info(
                f'NotifyIcon: {icon["title"]}\n'
                f'Handle: {icon["hwnd"]}\n'
                f'Rectangle: {icon["rect"]}'
            )
        except Exception as e:
            self.logger.error(f"Error showing notify icon info: {e}")

    def open_context_menu(self, element):
        """Open context menu for a regular tray element."""
        try:
            hwnd = element.handle
            # Send right-click message
            win32gui.PostMessage(hwnd, win32con.WM_CONTEXTMENU, hwnd, 0)
            self.logger.info(f"Sent context menu message to: {element.window_text()}")
        except Exception as e:
            self.logger.error(f"Error opening context menu: {e}")

    def open_notify_icon_menu(self, icon):
        """Open context menu for a NotifyIcon element."""
        try:
            hwnd = icon['hwnd']
            # Send NotifyIcon-specific messages
            win32gui.PostMessage(hwnd, WM_SHELLNOTIFY, 0, win32con.WM_CONTEXTMENU)
            self.logger.info(f"Sent notify icon context menu message to: {icon['title']}")
        except Exception as e:
            self.logger.error(f"Error opening notify icon menu: {e}")


def main():
    app = QApplication(sys.argv)
    inspector = SystemTrayInspector()
    inspector.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()