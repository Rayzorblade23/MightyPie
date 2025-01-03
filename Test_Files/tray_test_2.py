import ctypes
from ctypes import wintypes

# Load the user32 library for Windows API calls
user32 = ctypes.windll.user32

# Define necessary ctypes types
FindWindow = user32.FindWindowW
FindWindowEx = user32.FindWindowExW

# Define the window class names
SHELL_TRAY_WND = "Shell_TrayWnd"
TRAY_NOTIFY_WND = "TrayNotifyWnd"
SYS_PAGER = "SysPager"
TOOLBAR_WINDOW = "ToolbarWindow32"


def find_tray_window():
    """Finds the system tray toolbar window."""
    # Locate the Shell_TrayWnd
    tray_wnd = FindWindow(SHELL_TRAY_WND, None)
    if not tray_wnd:
        print("Shell_TrayWnd not found.")
        return None

    # Locate the TrayNotifyWnd (child of Shell_TrayWnd)
    tray_wnd = FindWindowEx(tray_wnd, None, TRAY_NOTIFY_WND, None)
    if not tray_wnd:
        print("TrayNotifyWnd not found.")
        return None

    # Locate the SysPager (child of TrayNotifyWnd)
    tray_wnd = FindWindowEx(tray_wnd, None, SYS_PAGER, None)
    if not tray_wnd:
        print("SysPager not found.")
        return None

    # Locate the ToolbarWindow32 (child of SysPager)
    tray_wnd = FindWindowEx(tray_wnd, None, TOOLBAR_WINDOW, None)
    if not tray_wnd:
        print("ToolbarWindow32 not found.")
        return None

    return tray_wnd


# Load the necessary Windows API libraries
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Define constants
TB_BUTTONCOUNT = 0x0418  # Message to get the button count
TB_GETBUTTON = 0x0417  # Message to get button information
PROCESS_VM_READ = 0x0010
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_ALL_ACCESS = 0x1F0FFF


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


def get_tooltips(tray_wnd):
    """Retrieves the tooltips of tray icons."""
    # Get the number of buttons in the toolbar
    button_count = user32.SendMessageW(tray_wnd, TB_BUTTONCOUNT, 0, 0)
    print(f"Number of tray icons: {button_count}")
    if button_count <= 0:
        return []

    # Get the process ID of the tray toolbar
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

    # Allocate memory in the target process for TBBUTTON
    button_size = ctypes.sizeof(TBBUTTON)
    remote_button = kernel32.VirtualAllocEx(
        h_process, None, button_size, 0x3000, 0x04
    )  # MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE
    if not remote_button:
        print("Failed to allocate memory in target process.")
        return []

    tooltips = []
    for i in range(button_count):
        # Send TB_GETBUTTON message to get button info
        user32.SendMessageW(tray_wnd, TB_GETBUTTON, i, remote_button)

        # Read the TBBUTTON structure from the process
        local_button = TBBUTTON()
        kernel32.ReadProcessMemory(
            h_process, remote_button, ctypes.byref(local_button), button_size, None
        )

        # Check if the button is hidden
        if local_button.fsState & 0x08:  # TBSTATE_HIDDEN
            continue

        # Read tooltip string from the process
        tooltip_buffer = ctypes.create_unicode_buffer(256)  # Adjust size as needed
        kernel32.ReadProcessMemory(
            h_process, local_button.iString, tooltip_buffer, 256 * ctypes.sizeof(wintypes.WCHAR), None
        )
        tooltips.append(tooltip_buffer.value)

    # Clean up allocated memory and close process handle
    kernel32.VirtualFreeEx(h_process, remote_button, 0, 0x8000)  # MEM_RELEASE
    kernel32.CloseHandle(h_process)

    return tooltips


# Step 1: Find the tray window
tray_window = find_tray_window()
if tray_window:
    # Step 2: Retrieve tooltips
    tray_tooltips = get_tooltips(tray_window)
    for idx, tooltip in enumerate(tray_tooltips, start=1):
        print(f"Icon {idx}: {tooltip}")
else:
    print("System Tray Toolbar Not Found.")
