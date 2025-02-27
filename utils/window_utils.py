# window_utils.py

import ctypes
import os
import sys
from ctypes import windll
from typing import Dict, Tuple, Optional, TypeAlias, Any

import psutil
import pythoncom
import win32api
import win32con
import win32gui
import win32process
import win32ui
from PIL import Image
from PyQt6.QtWidgets import QWidget, QMessageBox

from data.config import CONFIG
from data.window_manager import WindowManager
from utils.json_utils import JSONManager

cache_being_cleared = False

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


def update_icon_paths_in_cache():
    """Update the cache by removing entries with invalid or missing icon paths."""
    invalid_entries = [exe_name for exe_name, app_data in app_cache.items()
                       if not app_data.get('icon_path') or not os.path.exists(app_data['icon_path'])]

    for exe_name in invalid_entries:
        del app_cache[exe_name]
        print(f"Removed entry for {exe_name} due to invalid or missing icon path.")

    save_cache(app_cache)


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


def _get_pid_from_window_handle(hwnd):
    """Retrieve the Process ID (PID) for a given main_window handle."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
    except Exception as e:
        print(f"Error retrieving PID for main_window: {e}")
        return None


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
                    print(app_cache)
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


