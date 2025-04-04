import logging
import os
import subprocess
import time
import urllib.parse

import win32com.client
import win32con
import win32gui
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QApplication

# Configure logger
logger = logging.getLogger(__name__)


class WaitDialog(QDialog):
    """Dialog that shows a 'Please wait' message while operations are in progress."""

    def __init__(self, message="Please wait...", parent=None):
        """Initialize the wait dialog.

        Args:
            message: Message to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Operation in Progress")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(300, 100)

        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def closeWithDelay(self, msec=500):
        """Close the dialog after a delay.

        Args:
            msec: Delay in milliseconds before closing
        """
        QTimer.singleShot(msec, self.accept)


class ExplorerRestartManager:
    """Manager class for handling Windows Explorer windows operations."""

    @staticmethod
    def convert_url_to_path(url: str) -> str:
        """Convert a file URL to a Windows file path.

        Args:
            url: A file URL starting with 'file:///'

        Returns:
            Converted Windows file path
        """
        if not url.startswith("file:///"):
            return url

        path = url[8:]  # Remove the "file:///" prefix
        path = urllib.parse.unquote(path)  # Decode URL encoded paths (e.g., spaces as '%20')
        path = path.replace("/", "\\")  # Normalize slashes to Windows format

        return path

    @staticmethod
    def get_explorer_windows() -> tuple[list[str], list[dict]]:
        """Get the paths and positions of currently open Explorer windows.

        Returns:
            A tuple containing:
            - List of Explorer window paths
            - List of dictionaries with path and window rectangle information
        """
        shell = win32com.client.Dispatch("Shell.Application")
        explorer_windows = []
        window_positions = []

        for window in shell.Windows():
            try:
                if window.Name != "File Explorer":
                    continue

                path = window.LocationURL
                if not path:
                    continue

                path = ExplorerRestartManager.convert_url_to_path(path)

                # Ensure the path is valid
                if not os.path.exists(path):
                    logger.warning(f"Path does not exist: {path}")
                    continue

                # Get window handle and position
                hwnd = window.HWND
                rect = win32gui.GetWindowRect(hwnd)  # (left, top, right, bottom)

                window_positions.append({
                    'path': path,
                    'rect': rect
                })
                explorer_windows.append(path)

                logger.debug(f"Captured window: {path}, hwnd: {hwnd}, rect: {rect}")

            except Exception as e:
                logger.error(f"Error accessing window: {e}", exc_info=True)

        return explorer_windows, window_positions

    @staticmethod
    def restore_explorer_windows(window_positions: list[dict]) -> None:
        """Restore Explorer windows to their saved positions.

        Args:
            window_positions: List of dictionaries containing path and rect information
        """
        # First open all windows
        for window_info in window_positions:
            path = window_info['path']
            logger.info(f"Opening Explorer window for: {path}")
            subprocess.run(['explorer', path])
            time.sleep(0.5)  # Allow time for the window to open

        # Then position them
        ExplorerRestartManager._set_window_positions(window_positions)
        # Kill the explorer window that automatically opens
        ExplorerRestartManager._kill_windows_without_path()

    @staticmethod
    def _set_window_positions(window_positions: list[dict]) -> None:
        """Match open Explorer windows with saved positions and move them accordingly.

        Args:
            window_positions: List of dictionaries containing path and rect information
        """
        shell = win32com.client.Dispatch("Shell.Application")

        # Create a lookup dictionary for faster matching
        position_map = {info['path']: info['rect'] for info in window_positions}

        for window in shell.Windows():
            try:
                if window.Name != "File Explorer":
                    continue

                path = window.LocationURL
                if not path:
                    continue

                path = ExplorerRestartManager.convert_url_to_path(path)

                # Check if we have position information for this path
                if path in position_map:
                    hwnd = window.HWND
                    rect = position_map[path]
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]

                    logger.info(f"Positioning window for {path}, hwnd: {hwnd}, position: {rect}")
                    win32gui.MoveWindow(hwnd, rect[0], rect[1], width, height, True)

            except Exception as e:
                logger.error(f"Error positioning window: {e}", exc_info=True)

    @staticmethod
    def get_window_path_from_hwnd(hwnd: int) -> str | None:
        """Try to extract the window path from the hwnd.

        Args:
            hwnd: Window handle

        Returns:
            Window path if found, None otherwise
        """
        try:
            window_title = win32gui.GetWindowText(hwnd)

            if window_title and window_title.startswith("File Explorer"):
                # This assumes the path is at the end of the title
                # e.g., "Documents - File Explorer"
                parts = window_title.split(" - ")
                if len(parts) > 1:
                    return parts[0]  # Return the first part (the folder name)

        except Exception as e:
            logger.error(f"Error extracting window path from hwnd {hwnd}: {e}", exc_info=True)

        return None

    @staticmethod
    def restart_explorer() -> None:
        """Ask for confirmation before restarting explorer and reopen open windows."""
        # Ask for confirmation
        reply = QMessageBox.question(
            None,
            "Confirm Restart",
            "Are you sure you want to restart Explorer?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            logger.info("Explorer restart cancelled by user")
            return

        # Create and show the "Please wait" dialog
        wait_dialog = WaitDialog("Please wait while Explorer restarts and windows are restored...")
        wait_dialog.show()

        # Process the event loop to ensure the dialog is visible
        QApplication.processEvents()

        try:
            # Save explorer window state
            logger.info("Getting open Explorer windows before restart...")
            _, window_positions = ExplorerRestartManager.get_explorer_windows()

            # Restart Explorer
            logger.info("Stopping Explorer process...")
            subprocess.run(['powershell', 'Stop-Process', '-Name', 'explorer', '-Force'])
            time.sleep(1)  # Wait for explorer process to fully stop

            logger.info("Starting Explorer process...")
            subprocess.Popen(['explorer.exe'])
            time.sleep(2)  # Allow Explorer to fully restart

            # Restore windows
            logger.info(f"Restoring {len(window_positions)} Explorer windows...")
            ExplorerRestartManager.restore_explorer_windows(window_positions)
            logger.info("Explorer restart complete")

            # Schedule the dialog to close with a short delay
            wait_dialog.closeWithDelay(500)

        except Exception as e:
            logger.error(f"Error during Explorer restart: {e}", exc_info=True)
            wait_dialog.accept()  # Close the dialog in case of error

            # Show error message
            QMessageBox.critical(
                None,
                "Error",
                f"An error occurred while restarting Explorer: {str(e)}"
            )

    @staticmethod
    def _kill_windows_without_path():
        """Kills all Explorer windows without a valid path (e.g., 'This PC', 'Quick Access')."""
        shell = win32com.client.Dispatch("Shell.Application")

        for window in shell.Windows():
            try:
                if window.Name != "File Explorer":
                    continue

                # Check if the window has a valid path (this filters out "This PC", "Quick Access")
                path = window.LocationURL
                if not path:  # No valid path, so it's likely "This PC" or "Quick Access"
                    hwnd = window.HWND
                    # Send a close message to the window
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    logger.info(f"Closed window with hwnd: {hwnd}, no path: {path}")

            except Exception as e:
                logger.error(f"Error closing window: {e}", exc_info=True)
