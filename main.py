import atexit
import os
import signal
import sys
import tempfile
import threading
import warnings

from helper.keyboard_listener import HotkeyListener

warnings.simplefilter("ignore", UserWarning)
sys.coinit_flags = 2
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox, )

from data.config import CONFIG
from events import ShowWindowEvent
from functions.file_handling_utils import get_resource_path
from functions.taskbar_hide_utils import set_taskbar_opacity, show_taskbar
from global_mouse_filter import GlobalMouseFilter
from gui.pie_window import PieWindow

import ctypes


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

    def _show_messagebox(self):
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
    # Store instance in sys for global access
    sys._instance = SingleInstance()

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
    with open(get_resource_path("style.qss"), "r") as file:
        qss_template = file.read()

    # inserting style attributes from the config.py file
    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", CONFIG.ACCENT_COLOR_MUTED)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    # Apply the QSS to the application or widgets
    app.setStyleSheet(qss)

    # Create and show the main main_window
    window = PieWindow()

    # Install the GlobalMouseFilter
    global_mouse_filter = GlobalMouseFilter(window)
    app.installEventFilter(global_mouse_filter)

    # Show the main_window briefly and immediately hide it
    window.show()  # Make sure the main_window is part of the filtered_event loop
    window.hide()

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
