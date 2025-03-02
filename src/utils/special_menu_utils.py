import ctypes
import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtWidgets import QMessageBox, QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QVBoxLayout

from src.data.config import CONFIG
from src.gui.elements.toggle_switch import ToggleSwitch
from src.utils.icon_utils import get_icon


def is_portable():
    if not getattr(sys, 'frozen', False):
        return False
    exe_path = Path(sys.executable)
    program_files = os.environ.get('PROGRAMFILES', '')
    return not str(exe_path).startswith(program_files)


def get_startup_folder():
    return os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')


def show_message(title: str, message: str, is_error: bool = False):
    """Displays a message box using PyQt6."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical if is_error else QMessageBox.Icon.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.exec()


def add_to_startup():
    """Adds the program to Windows startup using Task Scheduler."""
    if not getattr(sys, 'frozen', False):  # Ensures this only runs for packaged executables
        show_message("Error", "Program is not running in frozen state (PyInstaller bundle).", is_error=True)
        return

    exe_path = sys.executable
    task_name = f"{CONFIG.INTERNAL_PROGRAM_NAME}Startup"
    create_task_cmd = f'schtasks /create /tn "{task_name}" /tr "{exe_path}" /sc ONLOGON /rl HIGHEST /f'

    try:
        subprocess.run(create_task_cmd, shell=True, check=True)
        show_message("Success", "The program has been added to startup successfully.")
    except subprocess.CalledProcessError as e:
        show_message("Error", f"Failed to create startup task:\n{e}", is_error=True)


def remove_from_startup():
    """Removes the scheduled task from Windows startup."""
    task_name = f"{CONFIG.INTERNAL_PROGRAM_NAME}Startup"
    remove_task_cmd = f'schtasks /delete /tn "{task_name}" /f'

    try:
        subprocess.run(remove_task_cmd, shell=True, check=True)
        show_message("Success", "The program has been removed from startup successfully.")
    except subprocess.CalledProcessError as e:
        show_message("Error", f"Failed to remove startup task:\n{e}", is_error=True)


def is_in_startup() -> bool:
    """Checks if the scheduled task exists in Windows Task Scheduler."""
    task_name = f"{CONFIG.INTERNAL_PROGRAM_NAME}Startup"
    check_task_cmd = f'schtasks /query /tn "{task_name}"'

    try:
        subprocess.run(check_task_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True  # Task exists
    except subprocess.CalledProcessError:
        return False  # Task does not exist


def _get_os_open_command():
    """Returns the appropriate file explorer command for the current OS."""
    os_commands = {
        "nt": "explorer",
        "posix": "xdg-open",
        "darwin": "open"
    }
    return os_commands.get(os.name, "xdg-open")


def _open_folder(path):
    """Generic function to open a folder in the system's file explorer."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    command = _get_os_open_command()
    QProcess.startDetached(command, [path])


def open_program_folder():
    """Opens the folder where the program is located."""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        program_dir = os.path.dirname(sys.executable)
    else:
        # Running in development
        program_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    _open_folder(program_dir)


def open_task_scheduler():
    """Opens the Task Scheduler management console without freezing the program."""
    try:
        subprocess.Popen('taskschd.msc', shell=True)
    except Exception as e:
        show_message("Error", f"Failed to open Task Scheduler: {e}", is_error=True)


def open_app_data_directory():
    """Opens the application data directory where configs are saved."""
    base_dirs = {
        "nt": os.path.join(os.environ.get('APPDATA', ''), CONFIG.INTERNAL_PROGRAM_NAME),
        "darwin": os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', CONFIG.INTERNAL_PROGRAM_NAME),
        "linux": os.path.join(os.path.expanduser('~'), '.config', CONFIG.INTERNAL_PROGRAM_NAME)
    }
    config_dir = base_dirs.get(os.name, os.path.abspath('../../..'))
    _open_folder(config_dir)


def create_folder_buttons(parent: QWidget) -> QHBoxLayout:
    # Button to open Startup Folder
    task_scheduler_button = QPushButton(" Task Scheduler", parent)
    task_scheduler_button.setToolTip("Open Task Scheduler")
    task_scheduler_button.setIcon(get_icon("schedule-time", is_inverted=True))
    task_scheduler_button.clicked.connect(lambda: [open_task_scheduler(), parent.hide()])
    # Button to open App Data Folder
    app_config_folder_button = QPushButton(" App Data", parent)
    app_config_folder_button.setToolTip(f"Open {CONFIG.INTERNAL_PROGRAM_NAME} App Data Folder")
    app_config_folder_button.setIcon(get_icon("folder-settings", is_inverted=True))
    app_config_folder_button.clicked.connect(lambda: [open_app_data_directory(), parent.hide()])
    # Button to open the Program Folder
    program_folder_button = QPushButton(" Program", parent)
    program_folder_button.setToolTip(f"Open {CONFIG.INTERNAL_PROGRAM_NAME} Program Folder")
    program_folder_button.setIcon(get_icon("folder-star", is_inverted=True))
    program_folder_button.clicked.connect(lambda: [open_program_folder(), parent.hide()])

    layout_app_folders = QHBoxLayout()
    layout_app_folders.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Ensure left alignment
    layout_app_folders.addWidget(task_scheduler_button)
    layout_app_folders.addWidget(app_config_folder_button)
    layout_app_folders.addWidget(program_folder_button)

    return layout_app_folders


def setup_startup_section(parent: QWidget) -> QHBoxLayout:
    # Settings for Startup
    startup_toggle = None
    label_not_admin = None
    layout_startup = QHBoxLayout()
    layout_startup.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Ensure left alignment
    # Check if running with admin privileges
    if ctypes.windll.shell32.IsUserAnAdmin():
        print("Running as admin. Making Startup Options available.")
        # Check if this is the Build
        if getattr(sys, 'frozen', False):
            startup_toggle = ToggleSwitch(
                "StartupToggle",
                label_text="Start with Windows",
                on_action=add_to_startup,
                off_action=remove_from_startup,
                parent=parent
            )
            startup_toggle.toggle.setCheckedWithoutAction(is_in_startup())
    else:
        label_not_admin = QLabel(" Run as admin to get 'Run At Startup' Toggle.")
    if startup_toggle:
        layout_startup.addWidget(startup_toggle)
    if label_not_admin:
        layout_startup.addWidget(label_not_admin)
    return layout_startup


def add_separator_line(layout: QVBoxLayout):
    """Adds a separator line to the layout."""
    line = QFrame()
    line.setFrameStyle(QFrame.Shape.HLine.value)
    line.setLineWidth(1)
    layout.addWidget(line)


def create_label(text: str) -> QLabel:
    """Creates and returns a label widget with the given text."""
    label = QLabel(text)
    label.setObjectName("titleLabel")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    return label