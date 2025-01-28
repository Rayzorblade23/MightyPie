# button_info.py
import json
import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox, QScrollArea,
                             QPushButton, QFrame)

from config import CONFIG


class ButtonInfo:
    def __init__(self):
        self.button_info_dict = {}
        self.config_file = "button_config.json"

        # Try to load from JSON first, fall back to default initialization
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_dict = json.load(f)
                    # Convert string keys back to integers
                    self.button_info_dict = {int(k): v for k, v in loaded_dict.items()}
            except Exception:
                self._initialize_tasks()
        else:
            self._initialize_tasks()

    def save_to_json(self):
        """Save current configuration to JSON file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.button_info_dict, f, indent=4)

    def _initialize_tasks(self):
        """Initialize with default configuration"""
        # Pre-defined tasks (example data)
        self.button_info_dict = {
            0: {
                "task_type": "program_window_fixed",
                "properties": {
                    "app_name": "Vivaldi",
                    "text_1": "",
                    "text_2": "",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": "vivaldi.exe"
                }
            },
            4: {
                "task_type": "program_window_fixed",
                "properties": {
                    "app_name": "Spotify",
                    "text_1": "",
                    "text_2": "",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": "spotify.exe"
                }
            },
            6: {
                "task_type": "program_window_fixed",
                "properties": {
                    "app_name": "Telegram Desktop",
                    "text_1": "",
                    "text_2": "Telegram Desktop",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": "telegram.exe"
                }
            }
        }

        # Explorer reserved spaces
        explorer_reserved_indexes = [8, 10, 12, 14]

        for i in explorer_reserved_indexes:
            if i not in self.button_info_dict:
                self.button_info_dict[i] = {
                    "task_type": "program_window_fixed",
                    "properties": {
                        "app_name": "Windows Explorer",
                        "text_1": "",
                        "text_2": "Windows Explorer",
                        "window_handle": -1,
                        "app_icon_path": "",
                        "exe_name": "explorer.exe"
                    }
                }

        # Fill in missing tasks
        for i in range(CONFIG.MAX_BUTTONS * CONFIG.NUM_PIE_TASK_SWITCHERS):
            if i not in self.button_info_dict:
                self.button_info_dict[i] = {
                    "task_type": "program_window_any",
                    "properties": {
                        "app_name": "",
                        "text_1": "",
                        "text_2": "",
                        "window_handle": -1,
                        "app_icon_path": "",
                        "exe_name": ""
                    }
                }

        # Save the initial configuration
        self.save_to_json()

    def __getitem__(self, index):
        """Allow direct access to tasks via index like task[index]."""
        return self.button_info_dict.get(index, None)

    def __setitem__(self, index, value):
        """Allow setting values directly and save to JSON"""
        self.button_info_dict[index] = value
        self.save_to_json()

    def __iter__(self):
        """Allow iteration over the keys of button_info_dict."""
        return iter(self.button_info_dict)

    def items(self):
        """Allow direct access to items like button_info.items()."""
        return self.button_info_dict.items()

    def keys(self):
        """Allow direct access to keys like button_info.keys()."""
        return self.button_info_dict.keys()

    def values(self):
        """Allow direct access to values like button_info.values()."""
        return self.button_info_dict.values()

    def get_task_indexes(self):
        """Returns a list of all task indexes."""
        return list(self.button_info_dict.keys())

    def filter_buttons(self, attribute, value):
        """
        Filters tasks based on a given attribute and value.

        :param attribute: Attribute to check (can be nested, e.g., 'properties.text_2')
        :param value: The value to match
        :return: A list of tasks matching the criteria
        """
        filtered = []
        for task_id, task in self.button_info_dict.items():
            keys = attribute.split('.')
            temp = task
            try:
                for key in keys:
                    temp = temp[key]
                if temp == value:
                    filtered.append(task)
            except KeyError:
                continue
        return filtered

    def get_all_tasks(self):
        """Returns all tasks."""
        return self.button_info_dict


# button_info_editor.py
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox)


class ButtonInfoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.button_info = ButtonInfo()

        # Available options for dropdowns
        self.task_types = ["program_window_fixed", "program_window_any"]

        # Get unique app names and exe names from existing configuration
        # self.app_names = set()
        self.exe_names = set()
        for task in self.button_info.values():
            # self.app_names.add(task["properties"]["app_name"])
            self.exe_names.add(task["properties"]["exe_name"])

        # Convert to sorted lists and ensure empty option is available
        # self.app_names = sorted(list(self.app_names)) + [""]
        self.exe_names = sorted(list(self.exe_names)) + [""]

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Button Info Editor')
        self.setGeometry(100, 100, 800, 600)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Create editors for each button
        for index in range(CONFIG.MAX_BUTTONS * CONFIG.NUM_PIE_TASK_SWITCHERS):
            button_frame = QFrame()
            button_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
            button_layout = QVBoxLayout(button_frame)

            # Header with button index
            header_layout = QHBoxLayout()
            header_label = QLabel(f"Button {index}")
            header_label.setStyleSheet("font-weight: bold;")
            header_layout.addWidget(header_label)
            button_layout.addLayout(header_layout)

            current_task = self.button_info[index]

            # Task type selector
            task_type_layout = QHBoxLayout()
            task_type_layout.addWidget(QLabel("Task Type:"))
            task_type_combo = QComboBox()
            task_type_combo.addItems(self.task_types)
            task_type_combo.setCurrentText(current_task["task_type"])
            task_type_layout.addWidget(task_type_combo)
            button_layout.addLayout(task_type_layout)

            # # App name selector
            # app_name_layout = QHBoxLayout()
            # app_name_layout.addWidget(QLabel("App Name:"))
            # app_name_combo = QComboBox()
            # app_name_combo.addItems(self.app_names)
            # app_name_combo.setCurrentText(current_task["properties"]["app_name"])
            # app_name_combo.setEditable(True)  # Allow custom entries
            # app_name_layout.addWidget(app_name_combo)
            # button_layout.addLayout(app_name_layout)

            # Exe name selector
            exe_name_layout = QHBoxLayout()
            exe_name_layout.addWidget(QLabel("Exe Name:"))
            exe_name_combo = QComboBox()
            exe_name_combo.addItems(self.exe_names)
            exe_name_combo.setCurrentText(current_task["properties"]["exe_name"])
            exe_name_combo.setEditable(True)  # Allow custom entries
            exe_name_layout.addWidget(exe_name_combo)
            button_layout.addLayout(exe_name_layout)

            # Store references to widgets for saving
            task_type_combo.setProperty("button_index", index)
            # app_name_combo.setProperty("button_index", index)
            exe_name_combo.setProperty("button_index", index)

            # Connect signals
            task_type_combo.currentTextChanged.connect(self.on_task_type_changed)
            # app_name_combo.currentTextChanged.connect(lambda text, idx=index: self.on_app_name_changed(text, idx))
            exe_name_combo.currentTextChanged.connect(lambda text, idx=index: self.on_exe_name_changed(text, idx))

            scroll_layout.addWidget(button_frame)

        # Add save button
        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self.save_changes)
        main_layout.addWidget(save_button)

    def on_task_type_changed(self, new_task_type):
        sender = self.sender()
        button_index = sender.property("button_index")
        self.button_info[button_index]["task_type"] = new_task_type
        # self.button_info.save_to_json()

    # def on_app_name_changed(self, new_app_name, button_index):
    #     self.button_info[button_index]["properties"]["app_name"] = new_app_name
    #     self.button_info.save_to_json()

    def on_exe_name_changed(self, new_exe_name, button_index):
        self.button_info[button_index]["properties"]["exe_name"] = new_exe_name
        # self.button_info.save_to_json()

    def save_changes(self):
        try:
            self.button_info.save_to_json()
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")


def main():
    import sys
    app = QApplication(sys.argv)
    editor = ButtonInfoEditor()
    editor.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
