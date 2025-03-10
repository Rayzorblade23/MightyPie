import argparse
import atexit
import ctypes
import faulthandler
import logging
import os
import signal
import sys
import tempfile
import threading
import traceback
from logging.handlers import RotatingFileHandler

from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox, )

from src.data.config import CONFIG
from src.events import ShowWindowEvent
from src.global_mouse_filter import GlobalMouseFilter
from src.gui.pie_window import PieWindow
from src.helper.keyboard_listener import HotkeyListener
from src.utils.file_handling_utils import get_resource_path
from src.utils.taskbar_hide_utils import set_taskbar_opacity, show_taskbar


def setup_crash_logging(log_file: str) -> None:
    """Sets up crash logging to a specific file."""
    class DualOutput:
        def __init__(self, file1, file2):
            self.file1 = file1
            self.file2 = file2

        def write(self, data):
            self.file1.write(data)
            self.file2.write(data)
            self.file1.flush()
            self.file2.flush()

        def flush(self):
            self.file1.flush()
            self.file2.flush()

        def fileno(self):
            return self.file1.fileno()

    # Store the original stderr
    original_stderr = sys.stderr

    # Create crash log file
    crash_file = open(log_file, "w")

    # Set up dual output for normal errors
    sys.stderr = DualOutput(crash_file, original_stderr)

    # Enable faulthandler to write directly to the crash file
    faulthandler.enable(file=crash_file, all_threads=True)

    def restore_stderr():
        if not crash_file.closed:
            crash_file.close()
        sys.stderr = original_stderr
        faulthandler.disable()

    atexit.register(restore_stderr)

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Set up log file path
    log_file = os.path.join(log_dir, 'mightypie.log')

    level = getattr(logging, log_level.upper(), logging.INFO)  # Convert string to logging level

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
    root_logger.setLevel(level)  # Set dynamically
    root_logger.addHandler(handler)

    # Also log to console during development
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    return root_logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="MightyPie Application")
    parser.add_argument(
        "--loglevel",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )
    args, _ = parser.parse_known_args()  # Ignore unknown args passed on restart
    return args


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
                self.lock_file_descriptor = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except OSError:
                self._show_messagebox()
        else:
            import fcntl
            self.lock_file_pointer = open(self.lockfile, 'w')
            try:
                fcntl.lockf(self.lock_file_pointer, fcntl.LOCK_EX | fcntl.LOCK_NB)
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
        # Stop hotkey listener if it exists
        if hasattr(self, 'hotkey_listener'):
            try:
                self.hotkey_listener.stop_listening()
            except Exception as e:
                logger.error(f"Error stopping hotkey listener: {e}")

        if sys.platform == 'win32':
            if hasattr(self, 'lock_file_descriptor'):
                os.close(self.lock_file_descriptor)
                if os.path.exists(self.lockfile):
                    os.unlink(self.lockfile)
            else:
                import fcntl
                if hasattr(self, 'lock_file_pointer'):
                    fcntl.lockf(self.lock_file_pointer, fcntl.LOCK_UN)
                    if not self.lock_file_pointer.closed:
                        self.lock_file_pointer.close()
                    if os.path.exists(self.lockfile):
                        os.unlink(self.lockfile)

    def release_for_restart(self):
        self.cleanup()


if __name__ == "__main__":

    try:
        # Initialize logging
        args = parse_args()
        logger = setup_logging(args.loglevel)
        logger.info(f"Logging setup complete with level: {args.loglevel}")
        logger.info("Starting MightyPie application")

        setup_crash_logging("crash_log.txt")

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
        hotkey_thread = threading.Thread(
            target=hotkey_listener.start_listening,
            daemon=True,
            name="HotkeyListenerThread"
        )
        hotkey_thread.start()

        sys._instance.hotkey_listener = hotkey_listener

        # main_window.auto_refresh()

        sys.exit(app.exec())

    except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            faulthandler.dump_traceback(file=sys.stderr)
            raise
