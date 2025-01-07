import ctypes
import sys
from ctypes import wintypes
from functools import partial

import psutil
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout

from config import CONFIG
from expanded_button import ExpandedButton

# Load necessary Windows API libraries
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

# Define constants
WM_MOUSEACTIVATE = 0x21
WM_LBUTTONDOWN = 0x0201  # Left mouse button down
WM_LBUTTONUP = 0x0202  # Left mouse button up
WM_LBUTTONDBLCLK = 0x0203  # Left mouse button double-click
WM_RBUTTONDOWN = 0x0204  # Right mouse button down
WM_RBUTTONUP = 0x0205  # Right mouse button up
WM_RBUTTONDBLCLK = 0x0206  # Right mouse button double-click
TB_BUTTONCOUNT = 0x0418
TB_GETBUTTON = 0x0417
PROCESS_VM_READ = 0x0010
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
TBSTATE_HIDDEN = 0x08  # Toolbar button state flag: Hidden
WM_CONTEXTMENU = 0x007B  # Context menu message


# Define ctypes structures
class TBBUTTON(ctypes.Structure):
    _fields_ = [
        ("iBitmap", wintypes.INT),
        ("idCommand", wintypes.INT),
        ("fsState", wintypes.BYTE),
        ("fsStyle", wintypes.BYTE),
        ("bReserved", wintypes.BYTE * 2),
        ("dwData", wintypes.LPARAM),
        ("iString", wintypes.LPARAM),
    ]


class TRAYDATA(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("Reserved", wintypes.DWORD * 2),
        ("hIcon", wintypes.HICON),
    ]


class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HBITMAP),
        ("hbmColor", wintypes.HBITMAP),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def get_tray_icons(tray_wnd):
    """Retrieve tooltips and associated process IDs of tray icons."""
    button_count = user32.SendMessageW(tray_wnd, TB_BUTTONCOUNT, 0, 0)
    if button_count <= 0:
        print("No tray icons found.")
        return []

    tray_pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(tray_wnd, ctypes.byref(tray_pid))
    h_process = kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_VM_OPERATION | PROCESS_VM_WRITE | PROCESS_QUERY_INFORMATION,
        False,
        tray_pid.value,
    )
    if not h_process:
        print("Failed to open process.")
        return []

    button_size = ctypes.sizeof(TBBUTTON)

    # Allocate memory for the button structure in the target process
    remote_button = kernel32.VirtualAllocEx(h_process, None, button_size, 0x3000, 0x04)
    if not remote_button:
        print("Failed to allocate memory in target process.")
        kernel32.CloseHandle(h_process)
        return []

    tray_icons = []
    try:
        # Process each button in the tray
        for i in range(button_count):
            user32.SendMessageW(tray_wnd, TB_GETBUTTON, i, remote_button)

            local_button = TBBUTTON()
            kernel32.ReadProcessMemory(h_process, remote_button, ctypes.byref(local_button), button_size, None)

            if local_button.fsState & TBSTATE_HIDDEN:
                continue

            traydata = TRAYDATA()
            kernel32.ReadProcessMemory(h_process, local_button.dwData, ctypes.byref(traydata), ctypes.sizeof(TRAYDATA), None)

            # Dynamically allocate a buffer for the tooltip based on length
            tooltip_buffer = ctypes.create_unicode_buffer(512)  # Increased buffer size
            read_size = kernel32.ReadProcessMemory(
                h_process, local_button.iString, tooltip_buffer, 512 * ctypes.sizeof(wintypes.WCHAR), None
            )

            # Handle error if the reading fails
            if read_size == 0:
                print(f"Failed to read tooltip for icon {tooltip_buffer.value}.")
                # continue

            process_id = wintypes.DWORD()
            user32.GetWindowThreadProcessId(traydata.hwnd, ctypes.byref(process_id))

            tray_icons.append({
                "tooltip": tooltip_buffer.value,
                "process_id": process_id.value,
                "is_visible": not (local_button.fsState & TBSTATE_HIDDEN),
                "hIcon": traydata.hIcon,  # Save the icon handle
                "hwnd": traydata.hwnd,  # Save the window handle of the tray icon
                "uCallbackMessage": traydata.uCallbackMessage,  # Save the callback message
                "uID": traydata.uID,  # Save the ID for use in callback
            })

    finally:
        # Ensure that the allocated memory is freed even if an error occurs
        kernel32.VirtualFreeEx(h_process, remote_button, 0, 0x8000)
        kernel32.CloseHandle(h_process)

    return tray_icons



# Step 1: Find the tray window
def find_tray_window():
    """Finds the system tray toolbar window."""
    SHELL_TRAY_WND = "Shell_TrayWnd"
    TRAY_NOTIFY_WND = "TrayNotifyWnd"
    SYS_PAGER = "SysPager"
    TOOLBAR_WINDOW = "ToolbarWindow32"

    tray_wnd = user32.FindWindowW(SHELL_TRAY_WND, None)
    if not tray_wnd:
        return None

    tray_wnd = user32.FindWindowExW(tray_wnd, None, TRAY_NOTIFY_WND, None)
    tray_wnd = user32.FindWindowExW(tray_wnd, None, SYS_PAGER, None)
    tray_wnd = user32.FindWindowExW(tray_wnd, None, TOOLBAR_WINDOW, None)

    return tray_wnd


def trigger_tray_icon_left_click(hwnd, uCallbackMessage, uID):
    """Trigger the full left-click interaction sequence for the tray icon, including WM_MOUSEACTIVATE."""
    if not hwnd:
        print("Invalid window handle (hwnd).")
        return

    # Ensure that the window can receive messages
    result = user32.IsWindow(hwnd)
    if not result:
        print(f"Window handle {hwnd} is invalid.")
        return

    # Simulate WM_MOUSEACTIVATE (Activate window on click)
    print(f"Sending WM_MOUSEACTIVATE to hwnd {hwnd}.")
    user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_MOUSEACTIVATE)  # Simulating Mouse Activate

    # Simulate the entire sequence of left-click interactions
    print(f"Sending WM_LBUTTONDOWN to hwnd {hwnd}.")
    user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_LBUTTONDOWN)  # Simulating Left Mouse Button Down

    print(f"Sending WM_LBUTTONUP to hwnd {hwnd}.")
    user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_LBUTTONUP)  # Simulating Left Mouse Button Up

    print(f"Sending WM_LBUTTONDBLCLK to hwnd {hwnd}.")
    user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_LBUTTONDBLCLK)  # Simulating Left Mouse Button Double Click

    print(f"Sending WM_LBUTTONUP to hwnd {hwnd}.")
    user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_LBUTTONUP)  # Simulating Left Mouse Button Up

    print(f"Simulated full left-click interaction and callback for tray icon with hwnd {hwnd}.")


def trigger_tray_icon_right_click(hwnd, uCallbackMessage, uID):
    """Trigger the full right-click interaction sequence for the tray icon, including WM_MOUSEACTIVATE."""
    if not hwnd:
        print("Invalid window handle (hwnd).")
        return

    # Ensure that the window can receive messages
    result = user32.IsWindow(hwnd)
    if not result:
        print(f"Window handle {hwnd} is invalid.")
        return

    # Simulate WM_MOUSEACTIVATE (Activate window on click)
    print(f"Sending WM_MOUSEACTIVATE to hwnd {hwnd}.")
    user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_MOUSEACTIVATE)  # Simulating Mouse Activate

    # Simulate the entire sequence of right-click interactions
    print(f"Sending WM_RBUTTONDOWN to hwnd {hwnd}.")
    user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_RBUTTONDOWN)  # Simulating Right Mouse Button Down

    print(f"Sending WM_RBUTTONUP to hwnd {hwnd}.")
    user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_RBUTTONUP)  # Simulating Right Mouse Button Up

    print(f"Sending WM_RBUTTONDBLCLK to hwnd {hwnd}.")
    user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_RBUTTONDBLCLK)  # Simulating Right Mouse Button Double Click

    print(f"Sending WM_RBUTTONUP to hwnd {hwnd}.")
    user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_RBUTTONUP)  # Simulating Right Mouse Button Up

    print(f"Simulated full right-click interaction and callback for tray icon with hwnd {hwnd}.")


def icon_to_qpixmap(hIcon):
    """Convert HICON to QPixmap with alpha channel support."""
    icon_info = ICONINFO()
    user32.GetIconInfo(hIcon, ctypes.byref(icon_info))

    # Extract the icon's bitmap
    bitmap = icon_info.hbmColor
    width = icon_info.xHotspot * 2
    height = icon_info.yHotspot * 2

    # Get bitmap data
    hdc = gdi32.CreateCompatibleDC(0)
    hBitmap = ctypes.c_void_p(bitmap)
    gdi32.SelectObject(hdc, hBitmap)

    # Create a bitmap header
    bitmap_header = BITMAPINFOHEADER()
    bitmap_header.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bitmap_header.biWidth = width
    bitmap_header.biHeight = -height  # Negative height for top-down DIB
    bitmap_header.biPlanes = 1
    bitmap_header.biBitCount = 32
    bitmap_header.biCompression = 0  # BI_RGB
    bitmap_header.biSizeImage = width * height * 4
    bitmap_header.biClrImportant = 0

    # Create buffer to store bitmap pixels
    buffer = ctypes.create_string_buffer(width * height * 4)

    # Get bitmap pixels
    gdi32.GetDIBits(hdc, hBitmap, 0, height, buffer, ctypes.byref(bitmap_header), 0)

    # Convert raw bytes to a PIL Image
    image_data = buffer.raw
    pil_image = Image.frombytes('RGBA', (width, height), image_data)

    # Handle 0-size images by creating a blank 16x16 image
    if pil_image.size == (0, 0):
        print("Warning: Encountered an image with size (0, 0). Creating a blank image.")
        pil_image = Image.new("RGBA", (16, 16), (128, 128, 128, 128))  # Transparent blank image

    # Swap R and B channels
    pixels = pil_image.load()
    for y in range(pil_image.height):
        for x in range(pil_image.width):
            r, g, b, a = pixels[x, y]
            pixels[x, y] = (b, g, r, a)

    # Convert PIL Image to QPixmap
    qimage = ImageQt(pil_image)  # Directly convert RGBA to QImage
    qpixmap = QPixmap.fromImage(qimage)

    # Clean up GDI objects
    gdi32.DeleteObject(hBitmap)
    gdi32.DeleteDC(hdc)

    return qpixmap

from PyQt6.QtCore import QTimer

class TrayIconButtonsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tray Icon Buttons")
        self.layout = QHBoxLayout()

        # Set up a timer to update tray icons every 5 seconds (5000 milliseconds)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_tray_icons)  # Trigger update_tray_icons function
        self.timer.start(5000)  # 5000 ms = 5 seconds

        # Initialize tray icon buttons
        self.tray_icons = []
        self.update_tray_icons()  # Initial load of tray icons

        self.setLayout(self.layout)

    def update_tray_icons(self):
        """Update tray icon buttons in the window."""
        tray_window = find_tray_window()
        if tray_window:
            tray_icons = get_tray_icons(tray_window)
            self.create_buttons(tray_icons)
        else:
            print("System Tray Toolbar Not Found.")

    def create_buttons(self, tray_icons):
        """Create buttons for tray icons, excluding system icons."""
        # Clear existing buttons first
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for icon_info in tray_icons:
            # Check if the icon belongs to a system process (e.g., explorer.exe)
            if is_system_process(icon_info["process_id"]):
                print(f"Skipping system icon with process ID: {icon_info['process_id']}")
                continue

            button = ExpandedButton(
                text="",
                object_name="TrayButton",
                size=(CONFIG.BUTTON_HEIGHT, CONFIG.BUTTON_HEIGHT)
            )

            # Connect the specific signals to their respective actions
            button.left_clicked.connect(partial(self.trigger_tray_icon, icon_info))
            button.right_clicked.connect(partial(self.trigger_tray_icon_context, icon_info))

            button.setIcon(QIcon(icon_to_qpixmap(icon_info["hIcon"])) )
            self.layout.addWidget(button)

    def trigger_tray_icon(self, icon_info):
        """Trigger the double-click interaction sequence for the tray icon."""
        hwnd, uCallbackMessage, uID = icon_info["hwnd"], icon_info["uCallbackMessage"], icon_info["uID"]
        print(f"Triggering double-click for hwnd: {hwnd} and uID: {uID}")
        user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_LBUTTONDOWN)
        user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_LBUTTONUP)
        user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_LBUTTONDBLCLK)
        user32.SetForegroundWindow(hwnd)

    def trigger_tray_icon_context(self, icon_info):
        """Trigger the right-click interaction sequence for the tray icon."""
        hwnd, uCallbackMessage, uID = icon_info["hwnd"], icon_info["uCallbackMessage"], icon_info["uID"]
        print(f"Triggering right-click for hwnd: {hwnd} and uID: {uID}")
        user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_RBUTTONDOWN)
        user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_RBUTTONUP)
        user32.PostMessageW(hwnd, uCallbackMessage, uID, WM_CONTEXTMENU)
        user32.SetForegroundWindow(hwnd)


def is_system_process(process_id):
    """Check if the process is a system process like explorer.exe."""
    try:
        proc = psutil.Process(process_id)
        if proc.name().lower() == 'explorer.exe':  # Checking for explorer.exe
            return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False


def main():
    app = QApplication(sys.argv)
    window = TrayIconButtonsWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
