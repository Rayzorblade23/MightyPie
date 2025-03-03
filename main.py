import atexit
import os
import signal
import sys
import tempfile
import threading
import warnings

from src.events import ShowWindowEvent
from src.global_mouse_filter import GlobalMouseFilter
from src.helper.keyboard_listener import HotkeyListener

warnings.simplefilter("ignore", UserWarning)
sys.coinit_flags = 2
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox, )

from src.data.config import CONFIG
from src.utils.file_handling_utils import get_resource_path
from src.utils.taskbar_hide_utils import set_taskbar_opacity, show_taskbar
from src.gui.pie_window import PieWindow

import ctypes

import logging
from logging.handlers import RotatingFileHandler


def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Set up log file path
    log_file = os.path.join(log_dir, 'mightypie.log')

    # Configure logging
    handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024 * 5,  # 5MB max file size
        backupCount=3  # Keep 3 backup files
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # Set default level
    root_logger.addHandler(handler)

    # Also log to console during development
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    return root_logger


def signal_handler(signal, frame):
    # Ensure taskbar is shown before exiting
    show_taskbar()
    # toggle_taskbar_autohide(False)
    sys.exit(0)


class SingleInstance:
    def __init__(self):
        self.lockfile = os.path.join(tempfile.gettempdir(), 'mightypie.lock')
        self._create_lock()
        atexit.register(self.cleanup)

    def _create_lock(self):
        if sys.platform == 'win32':
            try:
                if os.path.exists(self.lockfile):
                    os.unlink(self.lockfile)
                self.fd = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except OSError:
                self._show_messagebox()
        else:
            import fcntl
            self.fp = open(self.lockfile, 'w')
            try:
                fcntl.lockf(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                self._show_messagebox()

    @staticmethod
    def _show_messagebox():
        app = QApplication.instance()  # Check if QApplication already exists
        if not app:  # Create only if needed
            app = QApplication(sys.argv)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Already Running")
        msg.setText("It's already runnin', mate!")
        msg.exec()

        sys.exit(1)  # Ensure the program exits after showing the message

    def cleanup(self):
        if sys.platform == 'win32':
            if hasattr(self, 'fd'):
                os.close(self.fd)
                if os.path.exists(self.lockfile):
                    os.unlink(self.lockfile)
        else:
            import fcntl
            if hasattr(self, 'fp'):
                fcntl.lockf(self.fp, fcntl.LOCK_UN)
                if not self.fp.closed:
                    self.fp.close()
                if os.path.exists(self.lockfile):
                    os.unlink(self.lockfile)

    def release_for_restart(self):
        self.cleanup()


if __name__ == "__main__":
    # Initialize logging
    logger = setup_logging()
    logger.info("Starting MightyPie application")

    # Store instance in sys for global access
    try:
        sys._instance = SingleInstance()
    except Exception as e:
        logger.error(f"Failed to create single instance: {e}", exc_info=True)
        sys.exit(1)

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI awareness
    except AttributeError:
        pass  # Windows version does not support this API

    # Register signal handler for SIGINT (Ctrl+C) and SIGTERM (termination signals)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(CONFIG.INTERNAL_PROGRAM_NAME)

    set_taskbar_opacity(CONFIG.TASKBAR_OPACITY)

    # Load the QSS template
    with open(get_resource_path("assets/style.qss"), "r") as file:
        qss_template = file.read()

    # inserting style attributes from the config.py file
    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", CONFIG.ACCENT_COLOR_MUTED)
           .replace("{{any_btn_color}}", CONFIG.SHOW_ANY_WINDOW_BUTTON_BORDER_COLOR)
           .replace("{{prog_btn_color}}", CONFIG.SHOW_PROGRAM_BUTTON_BORDER_COLOR)
           .replace("{{launch_btn_color}}", CONFIG.LAUNCH_PROGRAM_BUTTON_BORDER_COLOR)
           .replace("{{call_func_color}}", CONFIG.CALL_FUNCTION_BUTTON_BORDER_COLOR)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    # Apply the QSS to the application or widgets
    app.setStyleSheet(qss)

    # Create and show the main main_window
    window = PieWindow()
    app.setProperty("main_window", window)

    # Install the GlobalMouseFilter
    global_mouse_filter = GlobalMouseFilter(window)
    app.installEventFilter(global_mouse_filter)

    event = ShowWindowEvent(window)
    # Post the filtered_event to the main thread
    QApplication.postEvent(window, event)

    # main_window.hide()  # Hide it right after showing

    # Hotkey Thread
    hotkey_listener = HotkeyListener(window)
    hotkey_thread = threading.Thread(target=hotkey_listener.start_listening, daemon=True)
    hotkey_thread.start()

    # main_window.auto_refresh()

    sys.exit(app.exec())
