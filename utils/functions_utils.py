import os
import subprocess
from typing import TYPE_CHECKING

import pyautogui
import win32api
import win32com.client
import win32con
import win32gui
import win32process
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCursor, QGuiApplication
from PyQt6.QtWidgets import QWidget, QMessageBox

from data.config import CONFIG
from data.window_manager import WindowManager
from utils.window_utils import _get_window_title

if TYPE_CHECKING:
    from gui.pie_window import PieWindow

last_minimized_hwnd = 0

manager = WindowManager.get_instance()


def get_explorer_windows_paths():
    """Get the paths of currently open Explorer windows."""
    shell = win32com.client.Dispatch("Shell.Application")
    explorer_windows = []

    for window in shell.Windows():
        try:
            if window.Name == "File Explorer":  # Only consider File Explorer windows
                # This will get the current folder path in the Explorer window
                path = window.LocationURL
                # Filter out empty or invalid paths
                if path:
                    # Convert file:/// path to a regular file path
                    path = path.replace("file:///", "").replace("/", "\\")
                    # Ensure the path is valid (i.e., it exists)
                    if os.path.exists(path):
                        explorer_windows.append(path)
        except Exception as e:
            print(f"Error accessing window: {e}")

    return explorer_windows


def restart_explorer():
    """Ask for confirmation before restarting explorer and reopen open windows."""
    # Step 1: Ask for confirmation
    reply = QMessageBox.question(
        None,
        "Confirm Restart",
        "Are you sure you want to restart Explorer?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )

    if reply == QMessageBox.StandardButton.Yes:
        # Step 2: Get the paths of open Explorer windows
        explorer_paths = get_explorer_windows_paths()

        # Step 3: Kill and restart Explorer
        subprocess.run("taskkill /f /im explorer.exe", shell=True)
        subprocess.run("start explorer.exe", shell=True)

        # Step 4: Reopen previously open Explorer windows using the tracked paths
        for path in explorer_paths:
            if path:
                # Open the folder with explorer
                subprocess.run(f'explorer "{path}"', shell=True)


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

        elif "explorer" in exe_path.lower():
            pyautogui.hotkey('win', 'e')

        else:
            # Redirect output to suppress terminal spam
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen(exe_path, stdout=devnull, stderr=devnull)
            print("Launched successfully.", exe_path)
    except Exception as e:
        print(f"An error occurred: {e}")


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


def minimize_window_at_cursor(main_window: "PieWindow"):
    """Minimizes the window at the cursor position."""
    if not hasattr(main_window, 'pie_menu_pos'):
        return

    cursor_pos = (main_window.pie_menu_pos.x(), main_window.pie_menu_pos.y())
    window_handle = win32gui.WindowFromPoint(cursor_pos)

    minimize_window_by_hwnd(window_handle)


def minimize_window_by_hwnd(hwnd: int):
    """Minimizes the specified window."""
    if hwnd and hwnd != win32gui.GetDesktopWindow():
        root_handle = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)

        if root_handle not in set(manager.get_open_windows_info().keys()):
            print("Hwnd is not among valid windows")
            return

        window_title = win32gui.GetWindowText(root_handle)
        print(f"Minimizing {window_title}")

        win32gui.ShowWindow(root_handle, win32con.SW_MINIMIZE)

        global last_minimized_hwnd
        last_minimized_hwnd = root_handle
    else:
        print("No valid window found.")


def toggle_maximize_window_at_cursor(pie_window: "PieWindow"):
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


def center_window_at_cursor(pie_window: "PieWindow"):
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


def focus_window_by_handle(hwnd):
    """Bring a main_window to the foreground and restore/maximize as needed."""
    if hwnd == win32gui.GetForegroundWindow():
        print(f"Window {hwnd} is already in the foreground.")
        return  # Avoid calling SetForegroundWindow again

    print(f"FOCUSING WINDOW {hwnd}")
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


def focus_all_explorer_windows():
    """Focuses all open Explorer Windows"""
    explorer_hwnds = []
    window_mapping = manager.get_open_windows_info()

    for hwnd, (title, exe_name, _) in window_mapping.items():
        # Explorer windows typically show up with "File Explorer" or "Windows Explorer" as the exe_name
        if exe_name == "explorer.exe":
            explorer_hwnds.append(hwnd)
            focus_window_by_handle(hwnd)


def close_window_at_cursor(main_window: "PieWindow") -> None:
    """Closes the window at the cursor position."""
    if not hasattr(main_window, 'pie_menu_pos'):
        return

    cursor_pos = (main_window.pie_menu_pos.x(), main_window.pie_menu_pos.y())

    window_handle = win32gui.WindowFromPoint(cursor_pos)

    # Get the root window handle instead of potentially a child control
    root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)

    if root_handle and root_handle != win32gui.GetDesktopWindow():
        print(f"Closing window at cursor: HWND {root_handle}")
        close_window_by_handle(root_handle)
    else:
        print("No valid window found under cursor.")


def close_window_by_handle(hwnd):
    """Close a window given its handle."""
    focus_window_by_handle(hwnd)
    try:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    except Exception as e:
        print(f"Could not close window with handle '{hwnd}': {e}")
