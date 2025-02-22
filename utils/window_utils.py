# window_utils.py

import ctypes
import os
import subprocess
import sys
from ctypes import windll
from typing import Dict, Tuple, Optional, TypeAlias, Any

import psutil
import pyautogui
import pythoncom
import win32api
import win32con
import win32gui
import win32process
import win32ui
from PIL import Image
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCursor, QGuiApplication
from PyQt6.QtWidgets import QWidget, QMessageBox

from data.config import CONFIG
from data.window_manager import WindowManager
from utils.json_utils import JSONManager

cache_being_cleared = False
last_minimized_hwnd = 0

APP_NAME = CONFIG.INTERNAL_PROGRAM_NAME
CACHE_FILENAME = CONFIG.INTERNAL_CACHE_FILENAME


def load_cache():
    """Load application name cache from file."""
    return JSONManager.load(APP_NAME, CACHE_FILENAME, default={})


def save_cache(cache):
    """Save application name cache to file."""
    if JSONManager.save(APP_NAME, CACHE_FILENAME, cache):
        print("Cache saved successfully.")
    else:
        print("Error saving cache file.")


def clear_cache(self):
    """Clear the cache by deleting the cache file."""
    reply = QMessageBox.question(
        self, "Reset Confirmation",
        "Are you sure you want to reset le Cache?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    if reply == QMessageBox.StandardButton.Yes:
        global cache_being_cleared
        cache_being_cleared = True

        cache_dir = JSONManager.get_config_directory(APP_NAME, config_type='cache')
        cache_file = os.path.join(cache_dir, CACHE_FILENAME)
        print(cache_file)

        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print("Cache file cleared successfully.")
            except Exception as e:
                print(f"Error clearing cache file: {e}")
        else:
            print("Cache file does not exist.")

        # Determine the program directory
        if hasattr(sys, '_MEIPASS'):  # Running as a compiled executable
            program_dir = os.path.dirname(sys.executable)
        else:  # Running as a script
            program_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Go up one level

        # Path to the app_icons folder
        icons_dir = os.path.join(program_dir, 'app_icons')
        print(f"Checking directory: {icons_dir}")  # For debugging purposes
        if os.path.exists(icons_dir):
            try:
                for filename in os.listdir(icons_dir):
                    file_path = os.path.join(icons_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    else:
                        os.rmdir(file_path)  # Remove any subdirectories if present
                print("Icons folder cleared successfully.")
            except Exception as e:
                print(f"Error clearing icons folder: {e}")
        else:
            print("Icons folder does not exist.")  # For debugging purposes

        global app_cache
        app_cache = load_cache()
        cache_being_cleared = False


app_cache = load_cache()

manager = WindowManager.get_instance()

# List to store HWNDs to exclude
hwnds_to_exclude = []
EXCLUDED_CLASS_NAMES = {"Progman", "AutoHotkeyGUI"}
DWM_WINDOW_CLOAKED_STATE = 14

# Custom type aliases
WindowInfo: TypeAlias = Tuple[str, str, int]  # (title, exe_name, instance)
WindowMapping: TypeAlias = Dict[int, WindowInfo]


def add_hwnd_to_exclude(widget: QWidget):
    """Adds the HWND of the given QWidget to the exclusion list."""
    global hwnds_to_exclude

    hwnd = int(widget.winId())  # Convert the voidptr to an integer
    hwnds_to_exclude.append(hwnd)


def get_filtered_list_of_windows(this_window: Optional[QWidget] = None) -> WindowMapping:
    temp_window_hwnds_mapping: WindowMapping = {}
    this_program_hwnd = int(this_window.winId()) if this_window else 0

    def enum_windows_callback(hwnd: int, _lparam: Any) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return

        window_title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)

        # Check window cloaked state
        is_cloaked = ctypes.c_int(0)
        ctypes.WinDLL("dwmapi").DwmGetWindowAttribute(
            hwnd, DWM_WINDOW_CLOAKED_STATE, ctypes.byref(is_cloaked), ctypes.sizeof(is_cloaked)
        )

        if _should_include_window(hwnd, window_title, class_name, is_cloaked.value, this_program_hwnd):
            entry, app_name = _get_window_info(hwnd)
            _clean_window_titles(temp_window_hwnds_mapping, entry, app_name)

    # Enumerate all top-level windows and pass each main_window's handle to the callback
    try:
        win32gui.EnumWindows(enum_windows_callback, None)
        # Assign instance numbers if windows have the same title
        temp_window_hwnds_mapping = assign_instance_numbers(temp_window_hwnds_mapping)

        # Update the main mapping dictionary with the filtered main_window handles
        manager.update_open_windows_info(temp_window_hwnds_mapping)

        return manager.get_open_windows_info()
    except Exception as e:
        print(f"Error getting windows: {e}")
        return {}


def _should_include_window(
        hwnd: int,
        window_title: str,
        class_name: str,
        is_cloaked: int,
        this_program_hwnd: int
) -> bool:
    """Check if a window should be included in the filtered list."""
    return all([
        win32gui.IsWindowVisible(hwnd),
        is_cloaked == 0,
        window_title.strip(),
        class_name not in EXCLUDED_CLASS_NAMES,
        hwnd != this_program_hwnd,
        hwnd not in hwnds_to_exclude
    ])


def _clean_window_titles(mapping: WindowMapping, entry: WindowMapping, app_name: str) -> None:
    """Update window titles in the mapping, removing unnecessary suffixes."""
    for hwnd, (window_title, exe_name, _) in entry.items():
        clean_title = window_title
        if exe_name == "explorer.exe" and " - File Explorer" in window_title:
            clean_title = window_title.replace(" - File Explorer", "")
        elif f" - {app_name}" in window_title:
            clean_title = window_title.replace(f" - {app_name}", "")

        mapping[hwnd] = (clean_title, exe_name, 0)


def assign_instance_numbers(temp_window_hwnds_mapping: Dict[int, Tuple[str, str, int]]) -> Dict[int, Tuple[str, str, int]]:
    """Assign unique instance numbers to windows with the same title and executable name."""

    # Get the current mapping of HWNDs to window info from the manager
    existing_mapping = manager.get_open_windows_info()

    # Create our result mapping
    result_mapping = {}

    # Track used instance numbers for each title/exe pair
    title_exe_mapping: Dict[Tuple[str, str], set] = {}

    # First step: Register all instances from the manager
    for hwnd, (title, exe, instance) in existing_mapping.items():
        key = (title, exe)
        if key not in title_exe_mapping:
            title_exe_mapping[key] = set()
        title_exe_mapping[key].add(instance)

    # Second step: Process each window
    for hwnd, (title, exe, instance) in temp_window_hwnds_mapping.items():
        # If window exists in manager, update its title and exe but keep the instance number
        if hwnd in existing_mapping:
            # print(f"Window {title} was there.")
            old_title, _, instance = existing_mapping[hwnd]  # Preserve the existing instance number
            new_title, _, _ = temp_window_hwnds_mapping[hwnd]  # Get the updated title and exe
            if new_title != old_title:
                instance = 0
            else:
                result_mapping[hwnd] = (new_title, exe, instance)
                continue

        key = (title, exe)
        if key not in title_exe_mapping:
            title_exe_mapping[key] = set()

        # Always try to find the next available instance number
        new_instance = 0
        while new_instance in title_exe_mapping[key]:
            # print(f"DEBUG: Incrementing instance for ({title}, {exe}) from {new_instance} to {new_instance + 1}")
            new_instance += 1

        # Add the new instance to our tracking set
        title_exe_mapping[key].add(new_instance)
        result_mapping[hwnd] = (title, exe, new_instance)

        # print(result_mapping)
    return result_mapping


def focus_all_explorer_windows():
    """Focuses all open Explorer Windows"""
    explorer_hwnds = []
    window_mapping = manager.get_open_windows_info()

    for hwnd, (title, exe_name, _) in window_mapping.items():
        # Explorer windows typically show up with "File Explorer" or "Windows Explorer" as the exe_name
        if exe_name == "explorer.exe":
            explorer_hwnds.append(hwnd)
            focus_window_by_handle(hwnd)


def _get_pid_from_window_handle(hwnd):
    """Retrieve the Process ID (PID) for a given main_window handle."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
    except Exception as e:
        print(f"Error retrieving PID for main_window: {e}")
        return None


def focus_window_by_handle(hwnd):
    """Bring a main_window to the foreground and restore/maximize as needed."""
    class_name = win32gui.GetClassName(hwnd)

    if class_name == "TaskManagerWindow":
        pyautogui.hotkey('ctrl', 'shift', 'esc')
        return

    if hwnd == win32gui.GetForegroundWindow() and CONFIG.HIDE_WINDOW_WHEN_ALREADY_FOCUSED:
        minimize_window_by_hwnd(hwnd)
        return

    try:
        # Get the current window placement
        placement = win32gui.GetWindowPlacement(hwnd)
        was_maximized = placement[1] == win32con.SW_MAXIMIZE  # Check if it was maximized

        # Maximize the window if it was maximized previously, otherwise restore it
        if was_maximized:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        try:
            # Get the current foreground window
            current_fore = win32gui.GetForegroundWindow()

            # Get thread IDs
            current_thread = win32api.GetCurrentThreadId()
            other_thread = win32process.GetWindowThreadProcessId(current_fore)[0]

            # Attach threads if necessary
            if current_thread != other_thread:
                win32process.AttachThreadInput(current_thread, other_thread, True)
                # time.sleep(0.1)  # Small delay to let Windows process the attachment
                try:
                    # Try multiple approaches to bring window to front
                    win32gui.BringWindowToTop(hwnd)
                    win32gui.SetForegroundWindow(hwnd)

                    # Alternative method using different flags
                    win32gui.SetWindowPos(hwnd,
                                          win32con.HWND_TOPMOST,
                                          0, 0, 0, 0,
                                          win32con.SWP_NOMOVE |
                                          win32con.SWP_NOSIZE |
                                          win32con.SWP_SHOWWINDOW)

                    # Remove topmost flag
                    win32gui.SetWindowPos(hwnd,
                                          win32con.HWND_NOTOPMOST,
                                          0, 0, 0, 0,
                                          win32con.SWP_NOMOVE |
                                          win32con.SWP_NOSIZE)

                except Exception as e:
                    print(f"Error during window manipulation: {e}")
                finally:
                    # Always detach threads
                    win32process.AttachThreadInput(current_thread, other_thread, False)
            else:
                # If in same thread, try direct approach
                try:
                    win32gui.SetForegroundWindow(hwnd)
                except Exception as e:
                    print(f"Error bringing window to front: {e}")
        except Exception as e:
            print(f"Error bringing window to front: {e}")
    except Exception as e:
        print(f"Could not focus main_window with handle '{_get_window_title(hwnd)}': {e}")


def close_window_by_handle(hwnd):
    """Close a window given its handle."""
    focus_window_by_handle(hwnd)
    try:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    except Exception as e:
        print(f"Could not close window with handle '{hwnd}': {e}")


def _get_window_info(window_handle):
    """Retrieve the application name, window title, exe_name, and default instance number 0 for a given main_window handle.

    Args:
        window_handle (any): The handle of the main_window for which to retrieve application info.

    Returns:
        dict: A dictionary where the key is the window_handle (int) and the value is a tuple (window_title, exe_name, 0).
    """
    result = {}
    window_title = _get_window_title(window_handle)

    if window_handle:
        pid = _get_pid_from_window_handle(window_handle)
        if pid:
            try:
                process = psutil.Process(pid)
                exe_path = process.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                print(f"Error accessing executable for PID {pid}: {e}")
                result[window_handle] = (window_title, "Unknown App", 0)
                return result

            if os.path.exists(exe_path):
                exe_name = os.path.basename(exe_path).lower()

                if exe_name in app_cache:
                    app_name = app_cache[exe_name]["app_name"]
                else:
                    app_name = _get_friendly_app_name(exe_path, exe_name)
                    app_cache[exe_name] = {"app_name": app_name, "icon_path": _get_window_icon(exe_path, window_handle),
                                           "exe_path": exe_path}
                    save_cache(app_cache)

                result[window_handle] = (window_title, exe_name, 0)
                return result, app_name
            else:
                print(f"Executable path does not exist: {exe_path}")
        result[window_handle] = (window_title, "Unknown App", 0)

    return result


def _get_friendly_app_name(exe_path: str, exe_name: str):
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
        if friendly_name.strip() and not "Unknown App":
            return friendly_name
        else:
            return os.path.splitext(exe_name)[0].capitalize()  # Remove the ".exe" extension
    except Exception as e:
        print(f"Error retrieving file description for {exe_path}: {e}")
        return os.path.splitext(exe_name)[0].capitalize()  # Remove the ".exe" extension


def hicon_to_image(icon_handle: int, size: tuple[int, int] = (32, 32)) -> Image.Image:
    """Converts an HICON to a PIL Image."""
    # Get a device context for the screen.
    screen_dc = win32gui.GetDC(0)
    device_context = win32ui.CreateDCFromHandle(screen_dc)
    memory_dc = device_context.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(device_context, size[0], size[1])
    memory_dc.SelectObject(bitmap)

    # Draw the icon into the memory DC.
    win32gui.DrawIconEx(memory_dc.GetSafeHdc(), 0, 0, icon_handle, size[0], size[1], 0, None, win32con.DI_NORMAL)

    bitmap_info = bitmap.GetInfo()
    bitmap_bits = bitmap.GetBitmapBits(True)

    image = Image.frombuffer('RGBA', (bitmap_info['bmWidth'], bitmap_info['bmHeight']),
                             bitmap_bits, 'raw', 'BGRA', 0, 1)

    # Clean up resources.
    try:
        memory_dc.DeleteDC()
        device_context.DeleteDC()
        win32gui.ReleaseDC(0, screen_dc)
        win32gui.DestroyIcon(icon_handle)
    except Exception as e:
        print(f"[DEBUG] Error during cleanup: {e}")

    return image


def _get_window_icon(exe_path: str, hwnd: int) -> Optional[str]:
    """Gets the icon for an open window using exe_path first, then WM_GETICON as fallback."""
    try:
        pythoncom.CoInitialize()
        icon_folder = "app_icons"
        if not os.path.exists(icon_folder):
            os.makedirs(icon_folder)

        # Try using exe_path method first
        if exe_path and os.path.exists(exe_path):
            try:
                large, small = win32gui.ExtractIconEx(exe_path, 0)
                if large or small:
                    icon_handle = large[0] if large else small[0]
                    image = hicon_to_image(icon_handle, size=(32, 32))
                    exe_name = os.path.basename(exe_path)
                    icon_filename = os.path.splitext(exe_name)[0] + '.png'
                    icon_path = os.path.join(icon_folder, icon_filename)
                    image.save(icon_path, format='PNG')
                    return icon_path
                else:
                    print(f"[DEBUG] No icon found in exe_path: {exe_path}")
            except Exception as e:
                print(f"[DEBUG] Error extracting icon from exe_path: {e}")
        else:
            print(f"[DEBUG] exe_path not provided or doesn't exist for hwnd {hwnd}")

        # Fallback: try using WM_GETICON method.
        print(f"[DEBUG] Falling back to WM_GETICON method for hwnd {hwnd}")
        icon_handle = win32gui.SendMessage(hwnd, win32con.WM_GETICON, win32con.ICON_BIG, 0)
        if icon_handle == 0:
            icon_handle = win32gui.SendMessage(hwnd, win32con.WM_GETICON, win32con.ICON_SMALL, 0)
        if icon_handle == 0:
            try:
                icon_handle = win32gui.GetClassLong(hwnd, win32con.GCL_HICON)
            except Exception:
                icon_handle = windll.user32.GetClassLongPtrW(hwnd, win32con.GCL_HICON)

        if icon_handle == 0:
            print(f"[DEBUG] No icon found using WM_GETICON method for hwnd {hwnd}")
            return None

        image = hicon_to_image(icon_handle, size=(32, 32))
        exe_name = os.path.basename(exe_path)  # Get exe_name for fallback case
        exe_name_no_ext = os.path.splitext(exe_name)[0]  # Remove .exe extension
        icon_path = os.path.join(icon_folder, f"{exe_name_no_ext}.png")  # Use exe_name without extension
        image.save(icon_path, format="PNG")
        print(f"[DEBUG] Icon extracted using WM_GETICON method saved as {icon_path}")
        return icon_path

    except Exception as e:
        print(f"[DEBUG] Error in _get_window_icon for hwnd {hwnd}: {e}")
        return None


def _get_window_title(hwnd):
    """Retrieve the title of the main_window for a given main_window handle."""
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception as e:
        print(f"Error retrieving main_window title for handle {hwnd}: {e}")
        return "Unknown Window Title"


def show_special_menu(menu: QWidget):
    # Get the current mouse position
    cursor_pos = QCursor.pos()

    screen = QGuiApplication.screenAt(cursor_pos)  # Detect screen at cursor position
    screen_geometry = screen.availableGeometry()  # Get the screen geometry

    # Get screen dimensions
    screen_left = screen_geometry.left()
    screen_top = screen_geometry.top()
    screen_right = screen_geometry.right()
    screen_bottom = screen_geometry.bottom()

    # Calculate initial new_x and new_y
    new_x = cursor_pos.x() - (menu.width() // 2)
    new_y = cursor_pos.y() - (menu.height() // 2)

    # Ensure main_window position stays within screen bounds
    corrected_x = max(screen_left, min(new_x, screen_right - menu.width()))
    corrected_y = max(screen_top, min(new_y, screen_bottom - menu.height()))

    # Normalize top left for other monitors
    corrected_x -= screen_left
    corrected_y -= screen_top

    if menu is not None:
        menu.move(corrected_x, corrected_y)

    # Make sure the window is on top and active
    menu.show()
    menu.setFocus()  # This should focus the menu


def center_window_at_cursor(pie_window: QWidget):
    """Centers the window under the cursor to the middle of its current monitor at 50% size."""
    if not hasattr(pie_window, 'pie_menu_pos'):
        return

    cursor_pos = (pie_window.pie_menu_pos.x(), pie_window.pie_menu_pos.y())
    window_handle = win32gui.WindowFromPoint(cursor_pos)

    if not window_handle or window_handle == win32gui.GetDesktopWindow():
        print("No valid window found under cursor")
        return

    root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)
    if not win32gui.IsWindowVisible(root_handle):
        print("Window is not visible")
        return

    monitor_info = win32api.MonitorFromPoint(cursor_pos, win32con.MONITOR_DEFAULTTONEAREST)
    monitor = win32api.GetMonitorInfo(monitor_info)
    monitor_rect = monitor['Monitor']

    screen_width = monitor_rect[2] - monitor_rect[0]
    screen_height = monitor_rect[3] - monitor_rect[1]
    new_width = screen_width // 2
    new_height = screen_height // 2
    new_x = monitor_rect[0] + (screen_width - new_width) // 2
    new_y = monitor_rect[1] + (screen_height - new_height) // 2

    win32gui.ShowWindow(root_handle, win32con.SW_RESTORE)
    win32gui.SetWindowPos(root_handle, None, new_x, new_y, new_width, new_height, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
    print("Window centered successfully on the correct monitor")


def toggle_maximize_window_at_cursor(pie_window: QWidget):
    if not hasattr(pie_window, 'pie_menu_pos'):
        return

    cursor_pos = (pie_window.pie_menu_pos.x(), pie_window.pie_menu_pos.y())
    window_handle = win32gui.WindowFromPoint(cursor_pos)

    if window_handle and window_handle != win32gui.GetDesktopWindow():
        root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)
        window_title = win32gui.GetWindowText(root_handle)

        # Check the current state of the window
        placement = win32gui.GetWindowPlacement(root_handle)
        is_maximized = placement[1] == win32con.SW_SHOWMAXIMIZED

        if is_maximized:
            print("Window is maximized. Restoring to normal.")
            win32gui.ShowWindow(root_handle, win32con.SW_RESTORE)
        else:
            print("Window is not maximized. Maximizing now.")
            win32gui.ShowWindow(root_handle, win32con.SW_MAXIMIZE)

        # Get the current foreground window
        current_fore = win32gui.GetForegroundWindow()

        # Get thread IDs
        current_thread = win32api.GetCurrentThreadId()
        other_thread = win32process.GetWindowThreadProcessId(current_fore)[0]

        def process_window_input():
            if current_thread != other_thread:
                win32process.AttachThreadInput(current_thread, other_thread, True)
                # No sleep here, handled by QTimer
                try:
                    # Try multiple approaches to bring window to front
                    win32gui.BringWindowToTop(root_handle)
                    win32gui.SetForegroundWindow(root_handle)

                    # Alternative method using different flags
                    win32gui.SetWindowPos(root_handle,
                                          win32con.HWND_TOPMOST,
                                          0, 0, 0, 0,
                                          win32con.SWP_NOMOVE |
                                          win32con.SWP_NOSIZE |
                                          win32con.SWP_SHOWWINDOW)

                    # Remove topmost flag
                    win32gui.SetWindowPos(root_handle,
                                          win32con.HWND_NOTOPMOST,
                                          0, 0, 0, 0,
                                          win32con.SWP_NOMOVE |
                                          win32con.SWP_NOSIZE)
                except Exception as e:
                    print(f"Error during window manipulation: {e}")
                finally:
                    # Always detach threads
                    win32process.AttachThreadInput(current_thread, other_thread, False)
            else:
                # If in same thread, try direct approach
                try:
                    win32gui.SetForegroundWindow(root_handle)
                except Exception as e:
                    print(f"Error bringing window to front: {e}")

            print("Window maximized successfully")

        # Defer the execution of window manipulation to prevent blocking
        QTimer.singleShot(100, process_window_input)

    else:
        print("No valid window found under cursor")


def minimize_window_at_cursor(pie_window: QWidget):
    if not hasattr(pie_window, 'pie_menu_pos'):
        return

    cursor_pos = (pie_window.pie_menu_pos.x(), pie_window.pie_menu_pos.y())

    window_handle = win32gui.WindowFromPoint(cursor_pos)

    valid_hwnds = set(manager.get_open_windows_info().keys())

    if window_handle and window_handle != win32gui.GetDesktopWindow():
        print("Valid window found")
        root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)
        print(f"Root window handle: {root_handle}")
        if root_handle not in valid_hwnds:
            print(f"Hwnd is not among valid windows")
            return

        window_title = win32gui.GetWindowText(root_handle)
        print(f"Window title: {window_title}")

        print("Attempting to minimize window...")
        win32gui.ShowWindow(root_handle, win32con.SW_MINIMIZE)

        global last_minimized_hwnd
        last_minimized_hwnd = root_handle
        print("Window minimized successfully")
    else:
        print("No valid window found under cursor")


def minimize_window_by_hwnd(hwnd):
    window_handle = hwnd

    if window_handle and window_handle != win32gui.GetDesktopWindow():
        print("Valid window found")
        root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)
        print(f"Root window handle: {root_handle}")

        window_title = win32gui.GetWindowText(root_handle)
        print(f"Window title: {window_title}")

        print("Attempting to minimize window...")
        win32gui.ShowWindow(root_handle, win32con.SW_MINIMIZE)

        global last_minimized_hwnd
        last_minimized_hwnd = root_handle
        print("Window minimized successfully")
    else:
        print("No valid window found under cursor")


def restore_last_minimized_window():
    """Restores a maximized window under the cursor and brings it to the foreground."""
    window_handle = last_minimized_hwnd

    print(window_handle)

    if window_handle and window_handle != win32gui.GetDesktopWindow():
        root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)

        # Check the current state of the window
        placement = win32gui.GetWindowPlacement(root_handle)
        is_minimized = placement[1] == win32con.SW_SHOWMINIMIZED

        if is_minimized:
            print("Window is minimized. Restoring...")
            win32gui.ShowWindow(root_handle, win32con.SW_RESTORE)

        # Get the current foreground window
        current_fore = win32gui.GetForegroundWindow()

        # Get thread IDs
        current_thread = win32api.GetCurrentThreadId()
        other_thread = win32process.GetWindowThreadProcessId(current_fore)[0]

        def process_window_input():
            if current_thread != other_thread:
                win32process.AttachThreadInput(current_thread, other_thread, True)
                # No sleep here, handled by QTimer
                try:
                    # Try multiple approaches to bring window to front
                    win32gui.BringWindowToTop(root_handle)
                    win32gui.SetForegroundWindow(root_handle)

                    # Alternative method using different flags
                    win32gui.SetWindowPos(root_handle,
                                          win32con.HWND_TOPMOST,
                                          0, 0, 0, 0,
                                          win32con.SWP_NOMOVE |
                                          win32con.SWP_NOSIZE |
                                          win32con.SWP_SHOWWINDOW)

                    # Remove topmost flag
                    win32gui.SetWindowPos(root_handle,
                                          win32con.HWND_NOTOPMOST,
                                          0, 0, 0, 0,
                                          win32con.SWP_NOMOVE |
                                          win32con.SWP_NOSIZE)
                except Exception as e:
                    print(f"Error during window manipulation: {e}")
                finally:
                    # Always detach threads
                    win32process.AttachThreadInput(current_thread, other_thread, False)
            else:
                # If in same thread, try direct approach
                try:
                    win32gui.SetForegroundWindow(root_handle)
                except Exception as e:
                    print(f"Error bringing window to front: {e}")

            print("Window restored successfully.")

        # Defer the execution of window manipulation to prevent blocking
        QTimer.singleShot(100, process_window_input)

    else:
        print("No valid window found.")


def launch_app(exe_path):
    """
    Launch an external application given its executable path.
    If the exe_path contains the word "spotify", it will use the Start Menu simulation method.

    :param exe_path: The path to the executable file.
    """
    try:
        # Check if exe_path contains 'spotify' (case-insensitive)
        if "spotify" in exe_path.lower():
            print("Detected Spotify. Using Start Menu simulation...")

            subprocess.run(['start', 'spotify:'], shell=True)

        else:
            # Redirect output to suppress terminal spam
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen(exe_path, stdout=devnull, stderr=devnull)
            print("Launched successfully.", exe_path)
    except Exception as e:
        print(f"An error occurred: {e}")
