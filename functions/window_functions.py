import ctypes
import json
import os
import subprocess
import time
from typing import Dict, Tuple

import psutil
import pyautogui
import win32api
import win32con
import win32gui
import win32process
import win32ui
from PIL import Image
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCursor, QGuiApplication
from PyQt6.QtWidgets import QMainWindow, QWidget

from config import CONFIG
from pie_menu import PieMenu
from special_menu import SpecialMenu
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


CACHE_FILE = CONFIG.CACHE_FILE

app_cache = load_cache()

manager = WindowManager.get_instance()


def get_filtered_list_of_windows(this_window: QWidget = None) -> Dict[int, Tuple[str, str, int]]:
    """Enumerate and retrieve a list of visible windows

    This is the window info, where:
        - The key is the HWND (int).
        - The values are a tuple containing:
            1. Window title (str): The title of the window.
            2. Exe name (str): The human-friendly name of the executable.
            3. Instance number (int): A unique instance number for this window.
    """
    temp_window_hwnds_mapping: Dict[int, Tuple[str, str, int]] = {}
    if this_window is not None:
        this_program_hwnd = int(this_window.winId())  # Exclude this program from the Switcher
    else:
        this_program_hwnd = 0

    def enum_windows_callback(hwnd, lparam):
        # Check if the main_window is visible
        if win32gui.IsWindowVisible(hwnd):

            raw_window_title = win32gui.GetWindowText(hwnd)
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
                    and raw_window_title.strip()  # Window must have a non-empty title
                    and class_name != "Progman"  # Exclude system windows like "Progman"
                    and class_name != "AutoHotkeyGUI"  # Exclude "AutoHotkey" windows
                    and hwnd != this_program_hwnd  # Exclude this program
                    and CONFIG.PROGRAM_NAME not in raw_window_title  # exclude all windows of this program

            ):
                # entry for temp_window_hwnds_mapping
                entry, app_name = _get_window_info(hwnd)
                # Remove the app_name from window_title if it is there
                for _hwnd, (_window_title, _exe_name, _) in entry.items():
                    _window_title = (
                        _window_title
                        if f" - {app_name}" not in _window_title
                        else _window_title.replace(f" - {app_name}", "")
                    )
                    # Now window_title is updated without the app_name suffix if applicable
                    temp_window_hwnds_mapping[hwnd] = _window_title, _exe_name, 0

    # Enumerate all top-level windows and pass each main_window's handle to the callback
    try:
        win32gui.EnumWindows(enum_windows_callback, None)

        # print(temp_window_hwnds_mapping)
        # print("###############\n")
        temp_window_hwnds_mapping = assign_instance_numbers(temp_window_hwnds_mapping)

        # Update the main mapping dictionary with the filtered main_window handles
        manager.update_window_hwnd_mapping(temp_window_hwnds_mapping)

        return manager.get_window_hwnd_mapping()
    except Exception as e:
        print(f"Error getting windows: {e}")
        return []


def assign_instance_numbers(temp_window_hwnds_mapping: Dict[int, Tuple[str, str, int]]) -> Dict[int, Tuple[str, str, int]]:
    """Assign unique instance numbers to windows with the same title and executable name."""

    # Get the current mapping of HWNDs to window info from the manager
    existing_mapping = manager.get_window_hwnd_mapping()

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


def focus_window_by_handle(hwnd):
    """Bring a main_window to the foreground and restore/maximize as needed."""
    try:
        # Get the current window placement
        placement = win32gui.GetWindowPlacement(hwnd)
        was_maximized = placement[1] == win32con.SW_MAXIMIZE  # Check if it was maximized

        # Maximize the window if it was maximized previously, otherwise restore it
        if was_maximized:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        # Bring the window to the front
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                              win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)

        # Bring the window to the front
        win32gui.SetForegroundWindow(hwnd)

        # Get the window's position and size
        rect = win32gui.GetWindowRect(hwnd)
        window_width = rect[2] - rect[0]

        # Simulate a click at the center of the window, 1 pixel down from the top
        center_x = rect[0] + window_width // 2
        click_y = rect[1] + 1  # 1 pixel down from the top

        # Simulate the click using PostMessage
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0, (click_y << 16) | center_x)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, (click_y << 16) | center_x)


    except Exception as e:
        print(f"Could not focus main_window with handle '{_get_window_title(hwnd)}': {e}")


def close_window_by_handle(hwnd):
    """Close a window given its handle."""
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
                    app_name = _get_friendly_app_name(exe_path)
                    app_cache[exe_name] = {"app_name": app_name, "icon_path": _get_window_icon(exe_path, window_handle),
                                           "exe_path": exe_path}
                    save_cache(app_cache)

                result[window_handle] = (window_title, exe_name, 0)
                return result, app_name
            else:
                print(f"Executable path does not exist: {exe_path}")
        result[window_handle] = (window_title, "Unknown App", 0)

    return result


def _get_friendly_app_name(exe_path: str):
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


def _get_window_icon(exe_path, hwnd):
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


def _get_window_title(hwnd):
    """Retrieve the title of the main_window for a given main_window handle."""
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception as e:
        print(f"Error retrieving main_window title for handle {hwnd}: {e}")
        return "Unknown Window Title"


def show_special_menu(menu: SpecialMenu):
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


def show_pie_window(pie_window: QMainWindow, pie_menu: PieMenu):
    """Display the main main_window and bring it to the foreground."""
    try:
        # Get the main_window handle
        hwnd = int(pie_window.winId())

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
        new_x = cursor_pos.x() - (pie_menu.width() // 2)
        new_y = cursor_pos.y() - (pie_menu.height() // 2)

        # Ensure main_window position stays within screen bounds
        corrected_x = max(screen_left, min(new_x, screen_right - pie_menu.width()))
        corrected_y = max(screen_top, min(new_y, screen_bottom - pie_menu.height()))

        # Normalize top left for other monitors
        corrected_x -= screen_left
        corrected_y -= screen_top

        if pie_menu is not None:
            pie_menu.move(corrected_x, corrected_y)

        # Set geometry for pie_window on the current screen
        pie_window.move(screen_geometry.topLeft())  # Move to the top-left of the screen
        pie_window.setFixedSize(screen_geometry.width(), screen_geometry.height())  # Ensure the window size matches screen size
        pie_window.view.setFixedSize(screen_geometry.width(), screen_geometry.height())  # Ensure view size matches screen size
        pie_window.scene.setSceneRect(0, 0, screen_geometry.width(), screen_geometry.height())

        # Prevents flashing a frame of the last window position when calling show()
        pie_window.setWindowOpacity(0)  # Make the window fully transparent
        pie_window.show()
        QTimer.singleShot(1, lambda: pie_window.setWindowOpacity(1))  # Restore opacity after a short delay

        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                              win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)

        return cursor_pos


    except Exception as e:
        print(f"Error showing the main main_window: {e}")


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

        # Attach threads if necessary
        if current_thread != other_thread:
            win32process.AttachThreadInput(current_thread, other_thread, True)
            time.sleep(0.1)  # Small delay to let Windows process the attachment
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
    else:
        print("No valid window found under cursor")


def minimize_window_at_cursor(pie_window: QWidget):
    if not hasattr(pie_window, 'pie_menu_pos'):
        return

    cursor_pos = (pie_window.pie_menu_pos.x(), pie_window.pie_menu_pos.y())

    window_handle = win32gui.WindowFromPoint(cursor_pos)

    if window_handle and window_handle != win32gui.GetDesktopWindow():
        print("Valid window found")
        root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)
        print(f"Root window handle: {root_handle}")

        window_title = win32gui.GetWindowText(root_handle)
        print(f"Window title: {window_title}")

        print("Attempting to minimize window...")
        win32gui.ShowWindow(root_handle, win32con.SW_MINIMIZE)
        print("Window minimized successfully")
    else:
        print("No valid window found under cursor")


def launch_app(exe_path):
    """
    Launch an external application given its executable path.
    If the exe_path contains the word "spotify", it will use the Start Menu simulation method.

    :param exe_path: The path to the executable file.
    """
    try:
        # Check if exe_path contains 'spotify' (case insensitive)
        if "spotify" in exe_path.lower():
            print("Detected Spotify. Using Start Menu simulation...")

            # Simulate opening Spotify from Start Menu (with quick sleeps)
            time.sleep(0.02)
            pyautogui.hotkey('ctrl', 'esc')  # Open Start menu
            time.sleep(0.02)
            pyautogui.write('Spotify')  # Type 'Spotify'
            time.sleep(0.02)
            pyautogui.press('enter')  # Press Enter
            print("Spotify launched using Start Menu simulation.")

        else:
            # Redirect output to suppress terminal spam
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen(exe_path, stdout=devnull, stderr=devnull)
            print("Vivaldi launched successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
