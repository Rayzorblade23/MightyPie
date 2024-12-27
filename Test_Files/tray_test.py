import ctypes
import struct
import psutil
from ctypes import wintypes
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel

# Windows API Constants
WM_LBUTTONDBLCLK = 0x0203
TB_BUTTONCOUNT = 1040
TB_GETBUTTON = 1042
TBSTATE_HIDDEN = 0x80

class TRAYDATA(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("Reserved", wintypes.DWORD * 2),
        ("hIcon", wintypes.HICON),
    ]

class TrayIconData:
    def __init__(self, toolTip, isVisible, processID, tray_data):
        self.toolTip = toolTip
        self.isVisible = isVisible
        self.processID = processID
        self.data = tray_data

    def __repr__(self):
        return f"TrayIconData(toolTip='{self.toolTip}', processID={self.processID}, isVisible={self.isVisible})"

def enum_system_tray():
    tray_list = []
    trayWnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
    if trayWnd:
        trayWnd = ctypes.windll.user32.FindWindowExW(trayWnd, None, "TrayNotifyWnd", None)
        if trayWnd:
            trayWnd = ctypes.windll.user32.FindWindowExW(trayWnd, None, "SysPager", None)
            if trayWnd:
                trayWnd = ctypes.windll.user32.FindWindowExW(trayWnd, None, "ToolbarWindow32", None)
                if trayWnd:
                    count = ctypes.windll.user32.SendMessageW(trayWnd, TB_BUTTONCOUNT, 0, 0)
                    if count > 0:
                        # Get the process ID for the tray
                        dwTrayPid = wintypes.DWORD()
                        ctypes.windll.user32.GetWindowThreadProcessId(trayWnd, ctypes.byref(dwTrayPid))
                        hProcess = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, dwTrayPid.value)  # PROCESS_ALL_ACCESS

                        if hProcess:
                            lpData = ctypes.windll.kernel32.VirtualAllocEx(hProcess, None, 1024, 0x1000, 0x04)  # MEM_COMMIT, PAGE_READWRITE
                            for i in range(count):
                                buttonInfo = struct.pack('I', 0)  # Placeholder, use actual button info here
                                trayInfo = TRAYDATA()
                                ctypes.windll.user32.SendMessageW(trayWnd, TB_GETBUTTON, i, ctypes.byref(buttonInfo))

                                # Read tray info into trayInfo
                                ctypes.windll.kernel32.ReadProcessMemory(hProcess, buttonInfo, ctypes.byref(trayInfo), ctypes.sizeof(TRAYDATA), None)

                                # Process the tooltip (simulating the tooltip read)
                                tooltip = "Sample Tooltip"
                                trayIcon = TrayIconData(tooltip, True, dwTrayPid.value, trayInfo)
                                tray_list.append(trayIcon)

                            ctypes.windll.kernel32.VirtualFreeEx(hProcess, lpData, 0, 0x8000)  # MEM_RELEASE
                        ctypes.windll.kernel32.CloseHandle(hProcess)
    return tray_list


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tray and Audio Management")
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        tray_list = enum_system_tray()

        if tray_list:
            first_tray = tray_list[0]
            button = QPushButton(first_tray.toolTip)
            button.clicked.connect(lambda: self.handle_button_click(first_tray))
            layout.addWidget(button)

            label = QLabel(f"Tooltip: {first_tray.toolTip}, Process ID: {first_tray.processID}")
            layout.addWidget(label)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def handle_button_click(self, tray_info):
        print(f"Button clicked for tray info: {tray_info}")


# Main Application Entry
def main():
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()


if __name__ == "__main__":
    main()
