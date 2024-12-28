import ctypes
import json
import os
import time
from typing import Dict

import psutil
import win32api
import win32con
import win32gui
import win32process
import win32ui
from PIL import Image
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QCursor, QGuiApplication
from PyQt6.QtWidgets import QWidget

from window_manager import WindowManager


# Cache Management
def load_cache():
    """Load application name cache from file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache file: {e}")
            return {}
    return {}


def save_cache(cache):
    """Save application name cache to file."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=4)
        print("Cache saved successfully.")
    except Exception as e:
        print(f"Error saving cache file: {e}")


CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_name_cache.json")

app_cache = load_cache()

manager = WindowManager.get_instance()


def get_pid_from_window_handle(hwnd):
    """Retrieve the Process ID (PID) for a given main_window handle."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
    except Exception as e:
        print(f"Error retrieving PID for main_window: {e}")
        return None


def focus_window_by_handle(hwnd):
    """Bring a main_window to the foreground and restore/maximize as needed."""
    try:

        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                              win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
    except Exception as e:
        print(f"Could not focus main_window with handle '{get_window_title(hwnd)}': {e}")

def close_window_by_handle(hwnd):
    """Close a window given its handle."""
    try:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    except Exception as e:
        print(f"Could not close window with handle '{hwnd}': {e}")


def get_friendly_app_name(exe_path: str):
    """Get the FileDescription (friendly app name) from the executable."""
    try:
        language, codepage = win32api.GetFileVersionInfo(
            exe_path, "\\VarFileInfo\\Translation"
        )[0]
        string_file_info = "\\StringFileInfo\\%04X%04X\\%s" % (
            language,
            codepage,
            "FileDescription",
        )
        friendly_name = win32api.GetFileVersionInfo(exe_path, string_file_info)
        return friendly_name if friendly_name else "Unknown App"
    except Exception as e:
        print(f"Error retrieving file description for {exe_path}: {e}")
        return "Unknown App"


def get_application_info(window_handle):
    """Retrieve the application name and icon path for a given main_window handle (and save friendly name).

    Args:
        window_handle (any): The handle of the main_window for which to retrieve application info.

    Returns:
        tuple: A tuple containing the application name (str) and icon path (str) if the main_window handle is valid and information is found.
        str: A string indicating either the main_window title (str) if the main_window handle is invalid, or an error message (str) if an exception occurs.
    """
    window_title = get_window_title(window_handle)
    try:
        if window_handle:
            pid = get_pid_from_window_handle(window_handle)
            if pid:
                process = psutil.Process(pid)
                try:
                    exe_path = process.exe()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                    print(f"Error accessing executable for PID {pid}: {e}")
                    return "Unknown App"
                if os.path.exists(exe_path):
                    exe_name = os.path.basename(exe_path).lower()
                    if exe_name in app_cache:
                        app_name = app_cache[exe_name]["app_name"]
                        icon_path = app_cache[exe_name]["icon_path"]
                    else:
                        icon_path = get_window_icon(exe_path, window_handle)
                        app_name = get_friendly_app_name(exe_path)
                        app_cache[exe_name] = {"app_name": app_name, "icon_path": icon_path}
                        save_cache(app_cache)
                    return app_name, icon_path

        return window_title
    except Exception as e:
        print(f"Error fetching application name for {window_title}: {e}")
        return "Unknown App, main_window title: " + window_title


def get_window_icon(exe_path, hwnd):
    try:
        if not exe_path:
            print(f"Executable path not found for hwnd: {hwnd}")
            return ""

        # Extract the icon from the executable
        large, small = win32gui.ExtractIconEx(exe_path, 0)

        if not large and not small:
            print(f"No icon found for executable: {exe_path}")
            return ""

        # Use the large icon (if available), else fallback to small
        icon_handle = large[0] if large else small[0]

        # Create a device context (DC)
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(hwnd))

        # Create a bitmap compatible with the main_window's device context
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)  # Specify 32x32 size

        # Create a compatible DC to draw the icon
        memdc = hdc.CreateCompatibleDC()
        memdc.SelectObject(hbmp)

        # Draw the icon onto the bitmap
        memdc.DrawIcon((0, 0), icon_handle)

        # Create the project subfolder if it doesn't exist
        icon_folder = 'app_icons'
        if not os.path.exists(icon_folder):
            os.makedirs(icon_folder)

        # Get the name of the executable without the ".exe" extension
        exe_name = os.path.basename(exe_path)
        icon_filename = os.path.splitext(exe_name)[0] + '.png'  # Changed to .png

        # Save the icon to the subfolder using PIL
        icon_path = os.path.join(icon_folder, icon_filename)

        # Convert bitmap to PIL Image
        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        im = Image.frombuffer(
            'RGBA',
            (32, 32),  # Explicitly set to 32x32
            bmpstr, 'raw', 'BGRA', 0, 1
        )

        # Save as PNG
        im.save(icon_path, format='PNG')

        # Cleanup the resources
        win32gui.DestroyIcon(icon_handle)

        print(f"Icon saved as {icon_path}.")
        return icon_path

    except Exception as e:
        print(f"Error fetching icon: {e}")
        return None


def get_window_title(hwnd):
    """Retrieve the title of the main_window for a given main_window handle."""
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception as e:
        print(f"Error retrieving main_window title for handle {hwnd}: {e}")
        return "Unknown Window Title"


def get_filtered_list_of_window_titles(this_window: QWidget = None):
    """Enumerate and retrieve a list of visible windows."""
    temp_window_titles_To_hwnds_map: Dict[int, int] = {}
    if this_window is not None:
        this_program_hwnd = int(this_window.winId())  # Exclude this program from the Switcher
    else:
        this_program_hwnd = 0

    def enum_windows_callback(hwnd, lparam):
        # Check if the main_window is visible
        if win32gui.IsWindowVisible(hwnd):

            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)

            # print(f"hwnd: {hwnd} and main_window title: {window_title}. This is the main_window functions script \n")

            # Check if the main_window is cloaked (hidden or transparent)
            isCloaked = ctypes.c_int(0)
            ctypes.WinDLL("dwmapi").DwmGetWindowAttribute(
                hwnd, 14, ctypes.byref(isCloaked), ctypes.sizeof(isCloaked)
            )
            # Apply filtering conditions to determine if we want to include this main_window

            if (
                    win32gui.IsWindowVisible(hwnd)  # Window must be visible
                    and isCloaked.value == 0  # Window must not be cloaked (hidden)
                    and window_title.strip()  # Window must have a non-empty title
                    and class_name != "Progman"  # Exclude system windows like "Progman"
                    and class_name != "AutoHotkeyGUI"  # Exclude "AutoHotkey" windows
                    and hwnd != this_program_hwnd  # Exclude this program
            ):
                if window_title in temp_window_titles_To_hwnds_map:
                    # Find the next available number by incrementing the count
                    count = 2
                    new_window_title = f"{window_title} ({count})"
                    while new_window_title in temp_window_titles_To_hwnds_map:
                        count += 1
                        new_window_title = f"{window_title} ({count})"
                    window_title = new_window_title

                temp_window_titles_To_hwnds_map[window_title] = hwnd

    # Enumerate all top-level windows and pass each main_window's handle to the callback
    try:
        win32gui.EnumWindows(enum_windows_callback, None)
        # Update the main mapping dictionary with the filtered main_window handles
        manager.update_window_titles_to_hwnds_map(temp_window_titles_To_hwnds_map)

        return list(manager.get_window_titles_to_hwnds_map().keys())
    except Exception as e:
        print(f"Error getting windows: {e}")
        return []


def show_pie_window(pie_window: QWidget, pie_menu: QWidget):
    """Display the main main_window and bring it to the foreground."""
    try:
        # Get the main_window handle
        hwnd = int(pie_window.winId())

        # Get the current mouse position
        cursor_pos = QCursor.pos()

        # Get screen dimensions
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        screen_left = screen_geometry.left()
        screen_top = screen_geometry.top()
        screen_right = screen_geometry.right()
        screen_bottom = screen_geometry.bottom()

        # Calculate initial new_x and new_y
        new_x = cursor_pos.x() - (pie_menu.width() // 2)
        new_y = cursor_pos.y() - (pie_menu.height() // 2)

        # Ensure main_window position stays within screen bounds
        corrected_x = max(screen_left, min(new_x, screen_right - pie_menu.width()))
        corrected_y = max(screen_top, min(new_y, screen_bottom - pie_menu.height()))

        if pie_menu is not None:
            pie_menu.move(corrected_x, corrected_y)

        # Prevents flashing a frame of the last window position when calling show()
        pie_window.setWindowOpacity(0)  # Make the window fully transparent
        pie_window.show()
        QTimer.singleShot(1, lambda: pie_window.setWindowOpacity(1))  # Restore opacity after a short delay

        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                              win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)



    except Exception as e:
        print(f"Error showing the main main_window: {e}")
