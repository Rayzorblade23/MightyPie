import ctypes
import atexit
import sys
import win32con
import winreg
import subprocess
import struct
import time


def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def elevate_to_admin():
    """Relaunch the script with administrator privileges."""
    if not is_admin():
        script = sys.argv[0]  # The current script
        params = ' '.join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit(0)  # Exit the current script


def toggle_taskbar_autohide(state: bool):
    """Toggle taskbar auto-hide on or off by modifying the registry."""
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3"

    try:
        # Open the registry key for reading and writing
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)

        # Read the current settings (REG_BINARY)
        original_settings_value, _ = winreg.QueryValueEx(reg_key, "Settings")
        print("Original registry value:", original_settings_value)

        # Convert the value to a mutable bytearray
        settings_value = bytearray(original_settings_value)

        # Modify the first byte of the second row (index 8 in the registry value)
        if state:
            settings_value[8] = 0x03  # Enable auto-hide (set to 0x03)
        else:
            settings_value[8] = 0x02  # Disable auto-hide (set to 0x02)

        # Write the modified settings back to the registry using winreg
        winreg.SetValueEx(reg_key, "Settings", 0, winreg.REG_BINARY, bytes(settings_value))

        print("Registry value modified successfully.")

        # Restart Explorer to apply the changes
        restart_explorer()

        # Wait for Explorer to restart fully (this can take a few moments)
        time.sleep(5)  # Wait for 5 seconds to let Explorer fully restart

    except PermissionError as e:
        print(f"Failed to toggle auto-hide due to permission error: {e}")
        raise
    except Exception as e:
        print(f"Failed to toggle auto-hide: {e}")
        raise
    finally:
        # Close the registry key after use
        winreg.CloseKey(reg_key)


def restart_explorer():
    """Restart Windows Explorer to apply taskbar changes."""
    subprocess.run("taskkill /f /im explorer.exe", shell=True)
    subprocess.run("start explorer.exe", shell=True)


def hide_taskbar():
    """Hide the Windows taskbar."""
    hwnd = get_taskbar_handle()
    if hwnd == 0:
        print("Taskbar window handle not found.")
    else:
        print(f"Taskbar handle: {hwnd}")
        ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_HIDE)


def show_taskbar():
    """Show the Windows taskbar."""
    hwnd = get_taskbar_handle()
    if hwnd == 0:
        print("Taskbar window handle not found.")
    else:
        print(f"Taskbar handle: {hwnd}")
        ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_SHOW)


def get_taskbar_handle():
    """Get the current taskbar window handle (retries if necessary)."""
    hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)

    # Retry to find the taskbar window handle after Explorer restart
    attempts = 5
    while hwnd == 0 and attempts > 0:
        print("Waiting for taskbar handle...")
        time.sleep(1)  # Wait for 1 second before retrying
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        attempts -= 1

    return hwnd


# Register cleanup function to restore the taskbar
atexit.register(show_taskbar)

# Elevate to admin if not already running as admin
elevate_to_admin()

try:
    print("Toggling auto-hide and hiding taskbar...")

    # First, toggle the auto-hide setting
    toggle_taskbar_autohide(True)  # Toggle to enable auto-hide

    # Then, hide the taskbar after the registry change
    hide_taskbar()

    input("Taskbar hidden. Press Enter to restore...")

except KeyboardInterrupt:
    print("Interrupted! Restoring taskbar...")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    raise
finally:
    print("Restoring taskbar...")
    show_taskbar()
    toggle_taskbar_autohide(False)  # Toggle back to disable auto-hide (if needed)
