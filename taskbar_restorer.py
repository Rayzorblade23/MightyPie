import ctypes
import win32con

def show_taskbar():
    """Show the Windows taskbar."""
    hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
    if hwnd == 0:
        print("Error: Taskbar window handle not found.")
        return

    result = ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_SHOW)
    if not result:
        print("Failed to show the taskbar.")
    else:
        print("Taskbar restored successfully.")

# Test restoring the taskbar
show_taskbar()
