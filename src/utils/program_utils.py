import os
import subprocess
import sys
import time
from typing import TYPE_CHECKING

import psutil
from PyQt6.QtCore import QCoreApplication, QPoint
from PyQt6.QtGui import QCursor, QScreen, QGuiApplication
from PyQt6.QtWidgets import QApplication, QWidget

if TYPE_CHECKING:
    from src.gui.pie_window import PieWindow


def restart_program():
    current_pid = os.getpid()
    print(f"Restarting. Current PID: {current_pid}")

    if hasattr(sys, '_instance'):
        sys._instance.release_for_restart()

    for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid and proc.info['cmdline']:
                if sys.argv[0] in proc.info['cmdline']:
                    print(f"Killing old instance: PID {proc.info['pid']}")
                    proc.terminate()
        except psutil.NoSuchProcess:
            pass

    new_process = subprocess.Popen([sys.executable] + sys.argv)
    print(f"New process started with PID: {new_process.pid}")

    time.sleep(1)
    os._exit(0)


def quit_program():
    QCoreApplication.exit()


def main_window_hide() -> None:
    main_window: "PieWindow" = QApplication.instance().property("main_window")
    main_window.hide()


# def open_pie_menu() -> None:
#     main_window: "PieWindow" = QApplication.instance().property("main_window")
#     main_window.active_child = 3
#     pie_menu = main_window.pie_menus_primary[main_window.active_child - 1]
#     show_event = ShowWindowEvent(main_window, pie_menu)
#     QApplication.postEvent(main_window, show_event)

def main_window_force_refresh(reassign_all_buttons: bool = False) -> None:
    main_window: "PieWindow" = QApplication.instance().property("main_window")
    main_window.force_refresh(reassign_all_buttons)


def position_window_at_cursor(window: QWidget, center: bool = True) -> None:
    """
    Positions a window relative to the cursor, keeping it within screen bounds.

    Args:
        window: The window to position
        center: If True, centers the window on cursor. If False, positions top-left at cursor.
    """
    # Get cursor position and window size
    cursor_pos = QCursor.pos()
    window_size = window.sizeHint()

    # Get screen geometry for the screen containing the cursor
    screen = QApplication.screenAt(cursor_pos)
    if screen is None:
        screen = QApplication.primaryScreen()
    screen_geometry = screen.geometry()

    # Calculate initial position
    if center:
        x = cursor_pos.x() - (window_size.width() // 2)
        y = cursor_pos.y() - (window_size.height() // 2)
    else:
        x = cursor_pos.x()
        y = cursor_pos.y()

    # Adjust position to keep within screen bounds
    x = max(screen_geometry.left(), min(x, screen_geometry.right() - window_size.width()))
    y = max(screen_geometry.top(), min(y, screen_geometry.bottom() - window_size.height()))

    # Move window
    window.move(QPoint(x, y))

def get_active_setup_screen() -> QScreen:
    """Return the screen with the largest available area (heuristic primary)."""
    screens = QGuiApplication.screens()
    if not screens:
        raise RuntimeError("No screens found")
    # Choose the screen with the maximum available area.
    return max(screens, key=lambda s: s.availableGeometry().width() * s.availableGeometry().height())

def get_screen_dpi(screen: QScreen) -> float:
    """Return the screen's logical and physical DPI as a tuple."""
    return screen.physicalDotsPerInch()