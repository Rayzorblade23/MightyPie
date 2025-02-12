import ctypes
import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QEvent, QTimer, pyqtSignal, QProcess
from PyQt6.QtGui import QPainter, QKeyEvent, QCursor
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, \
    QMessageBox

from gui.elements.toggle_switch import ToggleSwitch
from data.config import CONFIG
from events import taskbar_event
from functions.icon_utils import get_icon
from functions.taskbar_hide_utils import toggle_taskbar, is_taskbar_visible
from gui.invisible_ui import InvisibleUI
from gui.menus.special_menu_DF_monitor_selector import MonitorSetupMenu
from gui.menus.special_menu_app_shortcuts import AppSettingsMenu
from gui.menus.special_menu_windows_shortcuts import WindowsSettingsMenu


class SpecialMenu(QWidget):
    taskbar_visibility_changed = pyqtSignal(bool)  # Custom signal

    def __init__(self, obj_name: str = "", parent=None, main_window=None):

        super().__init__(parent)
        self.obj_name = obj_name
        self.main_window = main_window
        self.ignore_next_focus_out = False
        self.mouse_pressed_inside = False

        layout = QVBoxLayout(self)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.view.setObjectName(self.obj_name)
        self.setObjectName(self.obj_name)
        self.setup_window()

        toggles_layout = QVBoxLayout()

        # Taskbar toggle switch
        self.taskbar_toggle = ToggleSwitch(
            "TaskbarToggle",
            label_text="Toggle Taskbar Visibility",
            on_action=self.toggle_taskbar_action,
            off_action=self.toggle_taskbar_action,
            parent=self
        )
        toggles_layout.addWidget(self.taskbar_toggle)

        # Initialize the taskbar visibility based on current state
        self.initialize_taskbar_toggle()

        # Subscribe to the taskbar visibility event
        taskbar_event.visibility_changed.connect(self.update_taskbar_toggle)

        # self.clock = Clock()
        # self.clock_toggle = ToggleSwitch("ClockToggle",
        #                                  label_text="Clock!",
        #                                  on_action=lambda: (self.clock.show(),
        #                                                     self.clock_bg_toggle.setDisabled(False)),
        #
        #                                  off_action=lambda: (self.clock.hide(),
        #                                                      self.clock_bg_toggle.setDisabled(True)),
        #                                  parent=self)
        #
        # self.clock_bg_toggle = ToggleSwitch("ClockBgToggle",
        #                                     label_text="Clock: Opaque BG",
        #                                     on_action=lambda: self.clock.toggle_background(),
        #                                     off_action=lambda: self.clock.toggle_background(),
        #                                     parent=self)

        self.invisible_UI = InvisibleUI()
        self.invisible_UI_toggle = ToggleSwitch("InvisibleUIToggle",
                                                label_text="Invisible UI",
                                                on_action=lambda: (self.invisible_UI.show(),
                                                                   self.invisible_UI_visibility_toggle.setDisabled(False),
                                                                   self.invisible_UI_visibility_toggle.update()),

                                                off_action=lambda: (self.invisible_UI.hide(),
                                                                    self.invisible_UI_visibility_toggle.setDisabled(True),
                                                                    self.invisible_UI_visibility_toggle.update()),
                                                parent=self)

        self.invisible_UI_visibility_toggle = ToggleSwitch("InvisibleUIVisibilityToggle",
                                                           label_text="Make visible",
                                                           on_action=lambda: self.invisible_UI.setStyleSheet("background-color: red;"),
                                                           off_action=lambda: self.invisible_UI.setStyleSheet(
                                                               "background-color: rgba(20, 20, 255, 2);"),
                                                           parent=self)
        QTimer.singleShot(0, self.trigger_toggle)

        # Settings for Startup
        self.startup_toggle = None
        self.label_not_admin = None

        layout_startup = QHBoxLayout()
        layout_startup.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Ensure left alignment

        # Check if running with admin privileges
        if ctypes.windll.shell32.IsUserAnAdmin():
            print("Running as admin. Making Startup Options available.")
            # Check if this is the Build
            if getattr(sys, 'frozen', False):
                self.startup_toggle = ToggleSwitch(
                    "StartupToggle",
                    label_text="Start with Windows",
                    on_action=SpecialMenu.add_to_startup,
                    off_action=SpecialMenu.remove_from_startup,
                    parent=self
                )
                self.startup_toggle.toggle.setCheckedWithoutAction(SpecialMenu.is_in_startup())
        else:
            self.label_not_admin = QLabel(" Run as admin to get 'Run At Startup' Toggle.")

        if self.startup_toggle:
            layout_startup.addWidget(self.startup_toggle)
        if self.label_not_admin:
            layout_startup.addWidget(self.label_not_admin)
        toggles_layout.addLayout(layout_startup)

        # Button to open Startup Folder
        self.task_scheduler_button = QPushButton(" Task Scheduler", self)
        self.task_scheduler_button.setToolTip("Open Task Scheduler")
        self.task_scheduler_button.setIcon(get_icon("schedule-time", is_inverted=True))
        self.task_scheduler_button.clicked.connect(self.open_task_scheduler)

        # Button to open App Data Folder
        self.app_config_folder_button = QPushButton(" App Data", self)
        self.app_config_folder_button.setToolTip(f"Open {CONFIG.INTERNAL_PROGRAM_NAME} App Data Folder")
        self.app_config_folder_button.setIcon(get_icon("folder-settings", is_inverted=True))
        self.app_config_folder_button.clicked.connect(self.open_app_data_directory)

        # Button to open the Program Folder
        self.program_folder_button = QPushButton(" Program", self)
        self.program_folder_button.setToolTip(f"Open {CONFIG.INTERNAL_PROGRAM_NAME} Program Folder")
        self.program_folder_button.setIcon(get_icon("folder-star", is_inverted=True))
        self.program_folder_button.clicked.connect(self.open_program_folder)

        layout_app_folders = QHBoxLayout()
        layout_app_folders.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Ensure left alignment
        layout_app_folders.addWidget(self.task_scheduler_button)
        layout_app_folders.addWidget(self.app_config_folder_button)
        layout_app_folders.addWidget(self.program_folder_button)
        toggles_layout.addLayout(layout_app_folders)

        # self.tray_icon_menu = TrayIconButtonsWindow(parent=self)
        # layout.addWidget(self.tray_icon_menu)

        self.windows_settings_shortcuts = WindowsSettingsMenu(parent=self)

        self.app_shortcuts = AppSettingsMenu(parent=self)

        # # Create toggles for Clock
        # layout_clock = QHBoxLayout()
        # layout_clock.addWidget(self.clock_toggle)
        # layout_clock.addWidget(self.clock_bg_toggle)
        # toggles_layout.addLayout(layout_clock)

        # Create toggles for Invisible UI
        layout_invisUI = QHBoxLayout()
        layout_invisUI.addWidget(self.invisible_UI_toggle)
        layout_invisUI.addWidget(self.invisible_UI_visibility_toggle)
        toggles_layout.addLayout(layout_invisUI)

        layout.addLayout(toggles_layout)

        line = QFrame()
        line.setFrameStyle(QFrame.Shape.HLine.value)
        line.setLineWidth(1)
        layout.addWidget(line)

        windows_shortcuts_label = QLabel(f"Windows Shortcuts")
        windows_shortcuts_label.setObjectName("titleLabel")
        windows_shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(windows_shortcuts_label)
        layout.addWidget(self.windows_settings_shortcuts)

        line = QFrame()
        line.setFrameStyle(QFrame.Shape.HLine.value)
        line.setLineWidth(1)
        layout.addWidget(line)

        if CONFIG.SHOW_MONITOR_SECTION:
            self.monitor_shortcuts = MonitorSetupMenu(parent=self)

            monitors_label = QLabel(f"Monitor Switching")
            monitors_label.setObjectName("titleLabel")
            monitors_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(monitors_label)
            layout.addWidget(self.monitor_shortcuts)

            line = QFrame()
            line.setFrameStyle(QFrame.Shape.HLine.value)
            line.setLineWidth(1)
            layout.addWidget(line)

        app_shortcuts_label = QLabel(f"Mighty Pie Shortcuts")
        app_shortcuts_label.setObjectName("titleLabel")
        app_shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(app_shortcuts_label)
        layout.addWidget(self.app_shortcuts)

        self.setLayout(layout)

        # Set a minimum size or use resize() to adjust window size
        self.resize(self.sizeHint())  # Resize based on the sizeHint of the widget
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.scene.setSceneRect(0, 0, self.width(), self.height())

        # Set the widget to accept focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Install both application-wide and widget-specific event filters
        QApplication.instance().installEventFilter(self)
        self.installEventFilter(self)

    def initialize_taskbar_toggle(self):
        """Initialize the taskbar toggle based on the current visibility state."""
        if is_taskbar_visible():  # Check if the taskbar is visible
            self.taskbar_toggle.toggle.setCheckedWithoutAction(True)  # Taskbar is visible, toggle should be on
        else:
            self.taskbar_toggle.toggle.setCheckedWithoutAction(False)  # Taskbar is hidden, toggle should be off

    def toggle_taskbar_action(self):
        """Action to toggle the taskbar visibility."""
        toggle_taskbar()  # Call the function that toggles the taskbar visibility

    def update_taskbar_toggle(self, is_visible):
        """Update the taskbar toggle based on visibility."""
        if is_visible:
            self.taskbar_toggle.toggle.setCheckedWithoutAction(True)
        else:
            self.taskbar_toggle.toggle.setCheckedWithoutAction(False)

    def trigger_toggle(self):
        # self.clock_toggle.toggle.setChecked(False)  # Clock turned off by default
        # self.clock_toggle.toggle.toggle_switch()
        self.invisible_UI_toggle.toggle.setChecked(True)  # or False
        self.invisible_UI_toggle.toggle.toggle_switch()

    def setup_window(self):
        """Set up the main window properties."""
        self.setWindowTitle("Special Menu")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    @staticmethod
    def is_portable():
        if not getattr(sys, 'frozen', False):
            return False
        exe_path = Path(sys.executable)
        program_files = os.environ.get('PROGRAMFILES', '')
        return not str(exe_path).startswith(program_files)

    @staticmethod
    def get_startup_folder():
        return os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')

    @staticmethod
    def show_message(title: str, message: str, is_error: bool = False):
        """Displays a message box using PyQt6."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical if is_error else QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()

    @staticmethod
    def add_to_startup():
        """Adds the program to Windows startup using Task Scheduler."""
        if not getattr(sys, 'frozen', False):  # Ensures this only runs for packaged executables
            SpecialMenu.show_message("Error", "Program is not running in frozen state (PyInstaller bundle).", is_error=True)
            return

        exe_path = sys.executable
        task_name = f"{CONFIG.INTERNAL_PROGRAM_NAME}Startup"
        create_task_cmd = f'schtasks /create /tn "{task_name}" /tr "{exe_path}" /sc ONLOGON /rl HIGHEST /f'

        try:
            subprocess.run(create_task_cmd, shell=True, check=True)
            SpecialMenu.show_message("Success", "The program has been added to startup successfully.")
        except subprocess.CalledProcessError as e:
            SpecialMenu.show_message("Error", f"Failed to create startup task:\n{e}", is_error=True)

    @staticmethod
    def remove_from_startup():
        """Removes the scheduled task from Windows startup."""
        task_name = f"{CONFIG.INTERNAL_PROGRAM_NAME}Startup"
        remove_task_cmd = f'schtasks /delete /tn "{task_name}" /f'

        try:
            subprocess.run(remove_task_cmd, shell=True, check=True)
            SpecialMenu.show_message("Success", "The program has been removed from startup successfully.")
        except subprocess.CalledProcessError as e:
            SpecialMenu.show_message("Error", f"Failed to remove startup task:\n{e}", is_error=True)

    @staticmethod
    def is_in_startup() -> bool:
        """Checks if the scheduled task exists in Windows Task Scheduler."""
        task_name = f"{CONFIG.INTERNAL_PROGRAM_NAME}Startup"
        check_task_cmd = f'schtasks /query /tn "{task_name}"'

        try:
            subprocess.run(check_task_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True  # Task exists
        except subprocess.CalledProcessError:
            return False  # Task does not exist

    @staticmethod
    def _get_os_open_command():
        """Returns the appropriate file explorer command for the current OS."""
        os_commands = {
            "nt": "explorer",
            "posix": "xdg-open",
            "darwin": "open"
        }
        return os_commands.get(os.name, "xdg-open")

    @staticmethod
    def _open_folder(path):
        """Generic function to open a folder in the system's file explorer."""
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        command = SpecialMenu._get_os_open_command()
        QProcess.startDetached(command, [path])

    @staticmethod
    def open_program_folder():
        """Opens the folder where the program is located."""
        if getattr(sys, 'frozen', False):
            # Running in PyInstaller bundle
            program_dir = os.path.dirname(sys.executable)
        else:
            # Running in development
            program_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        SpecialMenu._open_folder(program_dir)

    @staticmethod
    def open_task_scheduler():
        """Opens the Task Scheduler management console without freezing the program."""
        try:
            subprocess.Popen('taskschd.msc', shell=True)
        except Exception as e:
            SpecialMenu.show_message("Error", f"Failed to open Task Scheduler: {e}", is_error=True)

    @staticmethod
    def open_app_data_directory():
        """Opens the application data directory where configs are saved."""
        base_dirs = {
            "nt": os.path.join(os.environ.get('APPDATA', ''), CONFIG.INTERNAL_PROGRAM_NAME),
            "darwin": os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', CONFIG.INTERNAL_PROGRAM_NAME),
            "linux": os.path.join(os.path.expanduser('~'), '.config', CONFIG.INTERNAL_PROGRAM_NAME)
        }
        config_dir = base_dirs.get(os.name, os.path.abspath('../..'))
        SpecialMenu._open_folder(config_dir)

    def closeEvent(self, event):
        """Hide the window instead of closing it."""
        self.hide()
        event.ignore()  # Prevent the default close behavior

    def mousePressEvent(self, event):
        """Track when mouse is pressed inside the window"""
        self.mouse_pressed_inside = True
        self.ignore_next_focus_out = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Reset mouse tracking flags"""
        self.mouse_pressed_inside = False
        self.ignore_next_focus_out = False
        super().mouseReleaseEvent(event)

    def focusOutEvent(self, event):
        """Improved focus out handling"""
        if self.ignore_next_focus_out:
            self.ignore_next_focus_out = False
            event.ignore()
            return

        # Get the current mouse position relative to the window
        mouse_pos = self.mapFromGlobal(QCursor.pos())

        # Check if the mouse is inside any child widget
        child_widget = self.childAt(mouse_pos)

        if not self.rect().contains(mouse_pos) or not child_widget:
            self.hide()
        else:
            event.ignore()

    def keyPressEvent(self, event: QKeyEvent):
        """Hide the window when pressing the Escape key."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)  # Pass other key events to the parent

    def eventFilter(self, obj, event):
        """Enhanced event filter for better click-outside detection"""
        if event.type() == QEvent.Type.MouseButtonPress:
            # Get mouse position relative to this widget
            mouse_pos = self.mapFromGlobal(QCursor.pos())

            # If the window is visible and click is outside
            if self.isVisible():
                # Check if click is outside the window
                if not self.rect().contains(mouse_pos):
                    self.hide()
                    return True  # Event handled
                else:
                    # Click is inside, set focus to the window
                    self.setFocus()
                    self.ignore_next_focus_out = True

        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.ignore_next_focus_out = False

        return super().eventFilter(obj, event)

    def showEvent(self, event):
        """Ensure proper focus when showing the window"""
        super().showEvent(event)
        self.setFocus()
        self.ignore_next_focus_out = False
        self.mouse_pressed_inside = False


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the QSS template
    with open("../../style.qss", "r") as file:
        qss_template = file.read()

    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", CONFIG.ACCENT_COLOR_MUTED)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    app.setStyleSheet(qss)

    special_menu = SpecialMenu("SpecialMenu")
    special_menu.show()  # Show SpecialMenu as a standalone window

    sys.exit(app.exec())
