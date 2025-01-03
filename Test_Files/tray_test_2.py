import ctypes
from ctypes import wintypes
from PIL import Image
from io import BytesIO

# Load necessary Windows API libraries
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

# Define constants
WM_LBUTTONDBLCLK = 0x0203  # Left mouse button double-click message
WM_MOUSEACTIVATE = 0x21
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_RBUTTONDBLCLK = 0x0206
TB_BUTTONCOUNT = 0x0418
TB_GETBUTTON = 0x0417
PROCESS_VM_READ = 0x0010
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
TBSTATE_HIDDEN = 0x08  # Toolbar button state flag: Hidden


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
    remote_button = kernel32.VirtualAllocEx(h_process, None, button_size, 0x3000, 0x04)
    if not remote_button:
        print("Failed to allocate memory in target process.")
        return []

    tray_icons = []
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
            print(f"Failed to read tooltip for icon {i}.")
            continue

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

    kernel32.VirtualFreeEx(h_process, remote_button, 0, 0x8000)
    kernel32.CloseHandle(h_process)

    return tray_icons




# Convert HICON to PIL Image
def icon_to_pil_image(hIcon):
    """Convert HICON to a PIL Image."""
    # Get icon info from user32.dll (corrected)
    icon_info = ICONINFO()
    user32.GetIconInfo(hIcon, ctypes.byref(icon_info))  # Corrected call to GetIconInfo

    # Extract the icon's bitmap
    bitmap = icon_info.hbmColor
    width = icon_info.xHotspot * 2
    height = icon_info.yHotspot * 2

    # Get bitmap data
    hdc = gdi32.CreateCompatibleDC(0)
    hBitmap = ctypes.c_void_p(bitmap)  # Ensure it's treated as a pointer handle
    gdi32.SelectObject(hdc, hBitmap)

    # Create a bitmap header
    bitmap_header = BITMAPINFOHEADER()
    bitmap_header.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bitmap_header.biWidth = width
    bitmap_header.biHeight = height
    bitmap_header.biPlanes = 1
    bitmap_header.biBitCount = 32
    bitmap_header.biCompression = 0
    bitmap_header.biSizeImage = width * height * 4
    bitmap_header.biClrImportant = 0

    # Create buffer to store bitmap pixels
    buffer = ctypes.create_string_buffer(width * height * 4)

    # Get bitmap pixels
    gdi32.GetDIBits(hdc, hBitmap, 0, height, buffer, ctypes.byref(bitmap_header), 0)

    # Convert to PIL Image
    image_data = buffer.raw
    pil_image = Image.frombytes('RGBA', (width, height), image_data)

    # Clean up
    gdi32.DeleteObject(hBitmap)
    gdi32.DeleteDC(hdc)

    return pil_image


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


# Simulate a click on the tray icon
def trigger_tray_icon(hwnd):
    """Simulate a left mouse button double-click on the tray icon."""
    user32.PostMessageW(hwnd, WM_LBUTTONDBLCLK, 0, 0)
    print(f"Simulated a double-click on tray icon with hwnd {hwnd}.")


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


# Example Usage:
tray_window = find_tray_window()
if tray_window:
    icons = get_tray_icons(tray_window)
    if icons:
        first_icon = icons[1]
        hwnd = first_icon["hwnd"]
        uCallbackMessage = first_icon["uCallbackMessage"]
        uID = first_icon["uID"]
        tooltip = first_icon["tooltip"]  # Retrieve the tooltip for this icon
        print(f"First tray icon hwnd: {hwnd}")
        print(f"Tooltip: {tooltip}")  # Print the tooltip text
        print(f"Callback message: {uCallbackMessage}, uID: {uID}")
        trigger_tray_icon_right_click(hwnd, uCallbackMessage, uID)
    else:
        print("No tray icons found.")
else:
    print("System Tray Toolbar Not Found.")
