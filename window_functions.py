import json
import os

import psutil
import win32api
import win32con
import win32gui
import win32process


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
                exe_path = process.exe()
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


CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "app_name_cache.json"
)
app_cache = load_cache()
