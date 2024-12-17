import ctypes
import json
import os
import time

import psutil
import win32api
import win32con
import win32gui
import win32process
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
    """Retrieve the Process ID (PID) for a given window handle."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
    except Exception as e:
        print(f"Error retrieving PID for window: {e}")
        return None


def focus_window_by_handle(hwnd):
    """Bring a window to the foreground and restore/maximize as needed."""
    try:
        win32gui.SetForegroundWindow(hwnd)
        placement = win32gui.GetWindowPlacement(hwnd)

        if placement[1] == win32con.SW_MINIMIZE:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        elif placement[1] == win32con.SW_SHOWMAXIMIZED:
            pass
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)

        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"Could not focus window with handle '{hwnd}': {e}")


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


def get_application_name(window_handle):
    """Retrieve the application name for a given window handle."""
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
                        app_name = app_cache[exe_name]
                    else:
                        app_name = get_friendly_app_name(exe_path)
                        app_cache[exe_name] = app_name
                        save_cache(app_cache)
                    return app_name
        return window_title
    except Exception as e:
        print(f"Error fetching application name for {window_title}: {e}")
        return "Unknown App, window title: " + window_title


def get_window_title(hwnd):
    """Retrieve the title of the window for a given window handle."""
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception as e:
        print(f"Error retrieving window title for handle {hwnd}: {e}")
        return "Unknown Window Title"


def get_filtered_list_of_window_titles(this_window: QWidget = None):
    """Enumerate and retrieve a list of visible windows."""
    temp_window_titles_To_hwnds_map: Dict[int, int] = {}

    if this_window is not None:
        this_program_hwnd = int(this_window.winId())  # Exclude this program from the Switcher
    else:
        this_program_hwnd = 0

    def enum_windows_callback(hwnd, lparam):
        # Check if the window is visible
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)

            # print(f"hwnd: {hwnd} and window title: {window_title}. This is the window functions script \n")

            # Check if the window is cloaked (hidden or transparent)
            isCloaked = ctypes.c_int(0)
            ctypes.WinDLL("dwmapi").DwmGetWindowAttribute(
                hwnd, 14, ctypes.byref(isCloaked), ctypes.sizeof(isCloaked)
            )
            # Apply filtering conditions to determine if we want to include this window
            if (
                    win32gui.IsWindowVisible(hwnd)  # Window must be visible
                    and isCloaked.value == 0  # Window must not be cloaked (hidden)
                    and window_title.strip()  # Window must have a non-empty title
                    and class_name != "Progman"  # Exclude system windows like "Progman"
                    and class_name != "AutoHotkeyGUI"  # Exclude "AutoHotkey" windows
                    and hwnd != this_program_hwnd  # Exclude this program
            ):
                if window_title in temp_window_titles_To_hwnds_map:
                    window_title += " (2)"
                temp_window_titles_To_hwnds_map[window_title] = hwnd

    # Enumerate all top-level windows and pass each window's handle to the callback
    try:
        win32gui.EnumWindows(enum_windows_callback, None)
        # Update the main mapping dictionary with the filtered window handles
        manager.update_window_titles_to_hwnds_map(
            temp_window_titles_To_hwnds_map)

        return list(manager.get_window_titles_to_hwnds_map().keys())
    except Exception as e:
        print(f"Error getting windows: {e}")
        return []


def show_window(window: QWidget):
    """Display the main window and bring it to the foreground."""
    try:
        # Get the window handle
        hwnd = int(window.winId())

        # Get the current mouse position
        cursor_pos = QCursor.pos()

        # Get screen dimensions
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        screen_left = screen_geometry.left()
        screen_top = screen_geometry.top()
        screen_right = screen_geometry.right()
        screen_bottom = screen_geometry.bottom()

        # Calculate initial new_x and new_y
        new_x = cursor_pos.x() - (window.width() // 2)
        new_y = cursor_pos.y() - (window.height() // 2)

        # Ensure window position stays within screen bounds
        corrected_x = max(screen_left, min(new_x, screen_right - window.width()))
        corrected_y = max(screen_top, min(new_y, screen_bottom - window.height()))

        # Move the window
        window.move(corrected_x, corrected_y)

        # Adjust the cursor position if it was moved
        if new_x != corrected_x or new_y != corrected_y:
            corrected_cursor_x = corrected_x + (window.width() // 2)
            corrected_cursor_y = corrected_y + (window.height() // 2)
            QCursor.setPos(corrected_cursor_x, corrected_cursor_y)

        # Ensure the window is visible and restored
        if not window.isVisible():
            window.show()

        # Get current foreground window and threads
        fg_window = win32gui.GetForegroundWindow()
        fg_thread, _ = win32process.GetWindowThreadProcessId(fg_window)
        this_thread = win32api.GetCurrentThreadId()

        # Detach any previous thread inputs to reset state
        try:
            ctypes.windll.user32.AttachThreadInput(this_thread, fg_thread, False)
        except (OSError, ctypes.WinError) as e:
            print(f"Error detaching thread input: {e}")

        # Multiple attempts to bring window to foreground
        for attempt in range(3):
            try:
                # Attach input threads
                ctypes.windll.user32.AttachThreadInput(this_thread, fg_thread, True)

                # Restore window if minimized
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

                # Try multiple methods to bring to foreground
                win32gui.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)

                # Detach input threads
                ctypes.windll.user32.AttachThreadInput(this_thread, fg_thread, False)

                break  # Success, exit attempts
            except Exception as e:
                print(f"Window focus attempt {attempt + 1} failed: {e}")
                time.sleep(0.1)  # Small delay between attempts

        # Final positioning to ensure visibility
        ctypes.windll.user32.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE, )
        ctypes.windll.user32.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE, )

    except Exception as e:
        print(f"Error showing the main window: {e}")
