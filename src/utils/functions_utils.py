import logging
import os
import subprocess
import time
import urllib.parse
from typing import TYPE_CHECKING

import pyautogui
import win32api
import win32com.client
import win32con
import win32gui
import win32process
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCursor, QGuiApplication, QScreen
from PyQt6.QtWidgets import QWidget, QMessageBox

from src.data.config import CONFIG
from src.data.window_manager import WindowManager
from src.utils.window_utils import _get_window_title

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.gui.pie_window import PieWindow

last_minimized_hwnd = 0

last_focused_explorer_hwnd = 0

manager = WindowManager.get_instance()


def get_explorer_windows_paths() -> tuple[list[str], list[dict[str, tuple[str, tuple[int, int, int, int]]]]]:
    """Get the paths and positions of currently open Explorer windows."""
    shell = win32com.client.Dispatch("Shell.Application")
    explorer_windows = []
    window_positions = []

    for window in shell.Windows():
        try:
            if window.Name == "File Explorer":  # Only consider File Explorer windows
                # This will get the current folder path in the Explorer window
                path = window.LocationURL
                if path:
                    # Convert file:/// path to a regular file path
                    if path.startswith("file:///"):
                        path = path[8:]  # Remove the "file:///" prefix
                        path = urllib.parse.unquote(path)  # Decode URL encoded paths (e.g., spaces as '%20')
                        path = path.replace("/", "\\")  # Normalize slashes to Windows format

                    # Ensure the path is valid (i.e., it exists)
                    if os.path.exists(path):
                        # Get window handle
                        hwnd = window.HWND

                        # Get the window position and size
                        rect = win32gui.GetWindowRect(hwnd)  # Returns (left, top, right, bottom)
                        window_positions.append({
                            'path': path,
                            'rect': rect
                        })

                        explorer_windows.append(path)

                        # Debugging: Print hwnd values
                        print(f"Captured window: {path}, hwnd: {hwnd}, rect: {rect}")

        except Exception as e:
            print(f"Error accessing window: {e}")

    return explorer_windows, window_positions


def restore_explorer_windows(window_positions: list[dict[str, tuple[str, tuple[int, int, int, int]]]]) -> None:
    """Restore Explorer windows to their saved positions."""
    # Open all the saved paths one by one with a small delay between them
    for window_info in window_positions:
        path = window_info['path']
        rect = window_info['rect']

        print(f"Opening Explorer window for: {path}")
        subprocess.run(['explorer', path])

        # Allow some time for the window to open before continuing
        time.sleep(1)  # Adjust this time if necessary, this gives a small gap

    # Now check all open Explorer windows and match by path
    shell = win32com.client.Dispatch("Shell.Application")
    windows = []
    for window in shell.Windows():
        try:
            if window.Name == "File Explorer":  # Only consider File Explorer windows
                path = window.LocationURL
                if path:
                    # Convert file:/// path to a regular file path
                    if path.startswith("file:///"):
                        path = path[8:]  # Remove the "file:///" prefix
                        path = urllib.parse.unquote(path)  # Decode URL encoded paths (e.g., spaces as '%20')
                        path = path.replace("/", "\\")  # Normalize slashes to Windows format

                    # Match the newly opened windows by path and restore position
                    for window_info in window_positions:
                        if window_info['path'] == path:
                            hwnd = window.HWND
                            rect = window_info['rect']
                            print(f"Found window for {path}, hwnd: {hwnd}, restoring position: {rect}")
                            win32gui.MoveWindow(hwnd, rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1], True)

                            # Adding delay to avoid overwhelming the system
                            time.sleep(0.5)  # You can adjust this delay if necessary
                            break  # Once the match is found, stop searching
        except Exception as e:
            print(f"Error accessing window: {e}")


def get_window_path_from_hwnd(hwnd: int) -> str | None:
    """Try to extract the window path from the hwnd."""
    try:
        # Get the window title (this might give us the path or part of it)
        window_title = win32gui.GetWindowText(hwnd)

        # If the title contains a path (i.e., it looks like a folder), return it
        # For instance, the title may look like "Folder - File Explorer (C:\Users\Username)"
        if window_title:
            if window_title.startswith("File Explorer"):
                # Extract path from title (if applicable)
                path = window_title.split(" - ")[-1]  # This assumes the path is at the end of the title
                return path
    except Exception as e:
        print(f"Error extracting window path from hwnd {hwnd}: {e}")

    return None  # If no path is found, return None


def restart_explorer() -> None:
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
        # Step 2: Get the paths and positions of open Explorer windows
        explorer_paths, window_positions = get_explorer_windows_paths()

        # Step 3: Kill and restart Explorer
        print("Stopping Explorer process...")
        subprocess.run(['powershell', 'Stop-Process', '-Name', 'explorer', '-Force'])
        time.sleep(1)  # Wait for explorer process to fully stop
        subprocess.Popen(['powershell', 'Start-Process', 'explorer.exe'])
        time.sleep(1)  # Allow Explorer to fully restart

        # Step 4: Reopen previously open Explorer windows and restore positions
        restore_explorer_windows(window_positions)


def launch_app(exe_path):
    """
    Launch an external application given its executable path.
    If the exe_path contains the word "spotify", it will use the Start Menu simulation method.

    :param exe_path: The path to the executable file.
    """
    try:
        # Check if exe_path contains 'spotify' (case-insensitive)
        if "spotify" in exe_path.lower():
            subprocess.run(['start', 'spotify:'], shell=True)

        elif "explorer" in exe_path.lower():
            pyautogui.hotkey('win', 'e')

        else:
            # using explorer.exe to avoid transferring admin rights
            subprocess.run(f'explorer.exe "{exe_path}"', shell=True)
            logger.info(f"Launched without admin privileges: {exe_path}")

    except Exception as e:
        logger.error(f"An error occurred when launching the app '{exe_path}': {e}")


def restore_last_minimized_window():
    """Restores a maximized window under the cursor and brings it to the foreground."""
    window_handle = last_minimized_hwnd

    if window_handle and window_handle != win32gui.GetDesktopWindow():
        root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)

        # Check the current state of the window
        placement = win32gui.GetWindowPlacement(root_handle)
        is_minimized = placement[1] == win32con.SW_SHOWMINIMIZED

        if is_minimized:
            logger.info("Window is minimized. Restoring...")
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
                    logger.error(f"Error during window manipulation: {e}")
                finally:
                    # Always detach threads
                    win32process.AttachThreadInput(current_thread, other_thread, False)
            else:
                # If in same thread, try direct approach
                try:
                    win32gui.SetForegroundWindow(root_handle)
                except Exception as e:
                    logger.error(f"Error bringing window to front: {e}")

            logger.debug("Window restored successfully.")

        # Defer the execution of window manipulation to prevent blocking
        QTimer.singleShot(100, process_window_input)

    else:
        logger.error("No valid window found.")


def focus_last_explorer_window() -> None:
    focus_window_by_handle(last_focused_explorer_hwnd)


def minimize_window_at_cursor(pie_window: "PieWindow"):
    """Minimizes the window at the cursor position."""
    if not hasattr(pie_window, 'pie_menu_pos'):
        return

    cursor_info = _get_cursor_screen_info(pie_window)
    if cursor_info is None:
        logger.warning("No valid screen information found. Exiting function.")
        return

    cursor_pos, _, _ = cursor_info

    window_handle = win32gui.WindowFromPoint(cursor_pos)

    minimize_window_by_hwnd(window_handle)


def minimize_window_by_hwnd(hwnd: int):
    """Minimizes the specified window."""
    if hwnd and hwnd != win32gui.GetDesktopWindow():
        root_handle = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)

        if root_handle not in set(manager.get_open_windows_info().keys()):
            logger.warning("Hwnd is not among valid windows")
            return

        logger.info(f"Minimizing {_get_window_title(root_handle)}")

        win32gui.ShowWindow(root_handle, win32con.SW_MINIMIZE)

        global last_minimized_hwnd
        last_minimized_hwnd = root_handle
    else:
        logger.warning("No valid window found.")


def toggle_maximize_window_at_cursor(pie_window: "PieWindow"):
    if not hasattr(pie_window, 'pie_menu_pos'):
        return

    cursor_info = _get_cursor_screen_info(pie_window)
    if cursor_info is None:
        logger.warning("No valid screen information found. Exiting function.")
        return

    cursor_pos, _, _ = cursor_info

    window_handle = win32gui.WindowFromPoint(cursor_pos)

    if window_handle and window_handle != win32gui.GetDesktopWindow():
        root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)

        if root_handle not in set(manager.get_open_windows_info().keys()):
            logger.warning("Hwnd is not among valid windows")
            return

        # Check the current state of the window
        placement = win32gui.GetWindowPlacement(root_handle)
        is_maximized = placement[1] == win32con.SW_SHOWMAXIMIZED

        if is_maximized:
            logger.info("Window is maximized. Restoring to normal.")
            win32gui.ShowWindow(root_handle, win32con.SW_RESTORE)
        else:
            logger.info("Window is not maximized. Maximizing now.")
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
                    logger.error(f"Error during window manipulation in toggle_maximize_window_at_cursor: {e}")
                finally:
                    # Always detach threads
                    win32process.AttachThreadInput(current_thread, other_thread, False)
            else:
                # If in same thread, try direct approach
                try:
                    win32gui.SetForegroundWindow(root_handle)
                except Exception as e:
                    logger.error(f"Error bringing window to front in toggle_maximize_window_at_cursor: {e}")

            logger.info(f"Maximized window: {_get_window_title(root_handle)}")

        # Defer the execution of window manipulation to prevent blocking
        QTimer.singleShot(100, process_window_input)

    else:
        logger.warning("No valid window found under cursor")


def center_window_at_cursor(pie_window: "PieWindow"):
    """Centers the window under the cursor to the middle of its current monitor at 50% size."""
    if not hasattr(pie_window, 'pie_menu_pos'):
        logger.warning("PieWindow has no 'pie_menu_pos' attribute. Exiting function.")
        return

    # Get information at cursor position
    cursor_info = _get_cursor_screen_info(pie_window)
    if cursor_info is None:
        logger.warning("No valid screen information found. Exiting function.")
        return

    physical_cursor_pos, scaling_factor, screen = cursor_info

    window_handle = win32gui.WindowFromPoint(physical_cursor_pos)

    if not window_handle or window_handle == win32gui.GetDesktopWindow():
        logger.warning("No valid window found under cursor.")
        return

    root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)

    if root_handle not in set(manager.get_open_windows_info().keys()):
        logger.warning("Hwnd is not among valid windows")
        return

    # Get the screen geometry directly
    screen_rect = screen.geometry()
    screen_width = screen_rect.width()
    screen_height = screen_rect.height()
    new_width = screen_width // 2
    new_height = screen_height // 2
    new_x = screen_rect.left() + (screen_width - new_width) // 2
    new_y = screen_rect.top() + (screen_height - new_height) // 2

    # Apply scaling
    if scaling_factor != 1.0:
        new_width = int(new_width * scaling_factor)
        new_height = int(new_height * scaling_factor)
        new_x = int(new_x * scaling_factor)
        new_y = int(new_y * scaling_factor)

    logger.info(f"Centering window on monitor: {screen_rect}")
    logger.info(f"New window size: ({new_width}, {new_height}) at position: ({new_x}, {new_y})")

    win32gui.ShowWindow(root_handle, win32con.SW_RESTORE)
    win32gui.SetWindowPos(root_handle, None, new_x, new_y, new_width, new_height, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)

    logger.info(f"Window {_get_window_title(root_handle)} centered successfully.")


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
    if hwnd == 0:
        logger.info("Tried focusing window with hwnd == 0.")
        return

    logger.info(f"FOCUSING WINDOW {hwnd}")

    class_name = win32gui.GetClassName(hwnd)
    window_title = _get_window_title(hwnd)
    logger.debug(f"Window class name: {class_name} and title: {window_title}")

    if class_name == "TaskManagerWindow":
        logger.debug("Detected Task Manager, sending hotkey to open it.")
        pyautogui.hotkey('ctrl', 'shift', 'esc')
        return

    if class_name == "CabinetWClass":
        global last_focused_explorer_hwnd
        last_focused_explorer_hwnd = hwnd

    if hwnd == win32gui.GetForegroundWindow() and not win32gui.IsIconic(hwnd):
        if CONFIG.HIDE_WINDOW_WHEN_ALREADY_FOCUSED:
            logger.debug(f"Window {window_title} is already focused. Hide instead.")
            minimize_window_by_hwnd(hwnd)
        return

    try:
        placement = win32gui.GetWindowPlacement(hwnd)
        was_maximized = placement[1] == win32con.SW_MAXIMIZE

        # Log window position and size
        rect = win32gui.GetWindowRect(hwnd)
        x, y, width, height = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
        logger.info(f"Window position: (x={x}, y={y}), size: (width={width}, height={height})")

        if was_maximized:
            logger.debug(f"Show window >>{window_title}<< maximized.")
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        else:
            logger.debug(f"Show window >>{window_title}<< normally.")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        try:
            current_fore = win32gui.GetForegroundWindow()
            logger.debug(f"Current foreground window: {_get_window_title(current_fore)}")

            current_thread = win32api.GetCurrentThreadId()
            other_thread = win32process.GetWindowThreadProcessId(current_fore)[0]
            logger.debug(f"Current thread ID: {current_thread}, Other thread ID: {other_thread}")

            if current_thread != other_thread:
                logger.debug("Attaching thread input to allow window focusing.")
                win32process.AttachThreadInput(current_thread, other_thread, True)

                try:
                    logger.debug(f"Trying to bring window >>{window_title}<< to top.")
                    win32gui.BringWindowToTop(hwnd)
                    win32gui.SetForegroundWindow(hwnd)

                    logger.debug(f"Setting window >>{window_title}<< as topmost.")
                    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)

                    logger.debug(f"Removing topmost flag from window >>{window_title}<<.")
                    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

                except Exception as e:
                    logger.error(f"Error during window manipulation in focus_window_by_handle: {e}")
                finally:
                    logger.debug("Detaching thread input.")
                    win32process.AttachThreadInput(current_thread, other_thread, False)
            else:
                logger.debug(f"Same thread, trying direct SetForegroundWindow call for >>{window_title}<<.")
                try:
                    win32gui.SetForegroundWindow(hwnd)
                except Exception as e:
                    logger.error(f"Error bringing window >>{window_title}<< to front in focus_window_by_handle: {e}")
        except Exception as e:
            logger.error(f"Error bringing window >>{window_title}<< to front in focus_window_by_handle: {e}")
    except Exception as e:
        logger.error(f"Could not focus window >>{window_title}<<: {e}")


def focus_all_explorer_windows():
    """Focuses all open Explorer Windows"""
    explorer_hwnds = []
    window_mapping = manager.get_open_windows_info()

    for hwnd, (title, exe_name, _) in window_mapping.items():
        # Explorer windows typically show up with "File Explorer" or "Windows Explorer" as the exe_name
        if exe_name == "explorer.exe":
            explorer_hwnds.append(hwnd)
            focus_window_by_handle(hwnd)


def close_window_at_cursor(pie_window: "PieWindow") -> None:
    """Closes the window at the cursor position."""
    if not hasattr(pie_window, 'pie_menu_pos'):
        return

    cursor_info = _get_cursor_screen_info(pie_window)
    if cursor_info is None:
        logger.warning("No valid screen information found. Exiting function.")
        return

    cursor_pos, _, _ = cursor_info

    window_handle = win32gui.WindowFromPoint(cursor_pos)

    # Get the root window handle instead of potentially a child control
    root_handle = win32gui.GetAncestor(window_handle, win32con.GA_ROOT)

    if root_handle and root_handle != win32gui.GetDesktopWindow():
        logger.info(f"Closing window at cursor: HWND {root_handle}")
        close_window_by_handle(root_handle)
    else:
        logger.warning("No valid window found under cursor.")


def close_window_by_handle(hwnd):
    """Close a window given its handle."""
    if hwnd not in set(manager.get_open_windows_info().keys()):
        logger.warning("Hwnd is not among valid windows")
        return

    focus_window_by_handle(hwnd)
    try:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        logger.info(f"Closing window: {_get_window_title(hwnd)}")
    except Exception as e:
        logger.error(f"Could not close window with handle '{hwnd}': {e}")


def _get_cursor_screen_info(pie_window) -> tuple[tuple[int, int], float, QScreen] | None:
    """
    Retrieves physical cursor position, scaling factor, and screen under the cursor.
    Adjusted for monitor scaling.
    Returns None if no screen is found under the cursor.
    """
    global_cursor_pos = pie_window.mapToGlobal(pie_window.pie_menu_pos)

    # Get the screen where Pie Window was opened
    screen = QGuiApplication.screenAt(global_cursor_pos)

    if not screen:
        logger.warning("No screen found under cursor. Exiting function.")
        return None

    scaling_factor = screen.devicePixelRatio()

    # Convert logical to physical coordinates (only for cursor position)
    physical_cursor_pos = (int(global_cursor_pos.x() * scaling_factor), int(global_cursor_pos.y() * scaling_factor))

    logger.debug(f"Returning physical_cursor_pos={physical_cursor_pos}, scaling_factor={scaling_factor}, screen={screen.name()}")

    return physical_cursor_pos, scaling_factor, screen
