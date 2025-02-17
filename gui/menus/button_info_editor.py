# button_info_editor.py

import logging
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFrame, QPushButton, QLabel

from data.button_info import ButtonInfo
from data.config import CONFIG
from gui.buttons.pie_button import BUTTON_TYPES
from utils.button_info_editor_utils import (
    update_window_title, create_scroll_area, create_column, get_direction, create_button_container,
    create_task_type_dropdown, create_exe_name_dropdown, create_texts_layout, create_dropdowns_layout, reset_single_frame, reset_to_defaults
)
from utils.icon_utils import get_icon
from utils.json_utils import JSONManager

logging.basicConfig(level=logging.DEBUG)


class ButtonInfoEditor(QWidget):
    def __init__(self) -> None:
        """Initializes the ButtonInfoEditor with necessary setups."""
        print("Starting ButtonInfoEditor init")  # Debug
        print(f"Current thread: {QThread.currentThread()}")  # Debug
        super().__init__()
        self.button_info = ButtonInfo.get_instance()
        print(f"ButtonInfo instance: {id(self.button_info)}")  # Debug

        # Available options for dropdowns
        self.task_types = list(BUTTON_TYPES.keys())
        self.apps_info = JSONManager.load(CONFIG.INTERNAL_PROGRAM_NAME, "apps_info_cache.json", default={})
        self.exe_names = sorted([(exe_name, app_info["app_name"]) for exe_name, app_info in self.apps_info.items()])
        self.init_ui()

    def init_ui(self) -> None:
        """Sets up the user interface components."""
        self.setWindowTitle('Button Info Editor')
        self.setGeometry(100, 100, 1500, 860)

        main_layout = QVBoxLayout(self)
        scroll, scroll_layout = create_scroll_area()
        main_layout.addWidget(scroll)

        num_columns = CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY + CONFIG.INTERNAL_NUM_PIE_MENUS_SECONDARY
        buttons_per_column = CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU

        for col in range(num_columns):
            column_widget, column_layout = create_column(col, buttons_per_column, self.create_button_frame)
            scroll_layout.addWidget(column_widget)

        button_container = create_button_container(self.reset_to_defaults, self.save_changes)
        main_layout.addLayout(button_container)

    def create_button_frame(self, index: int, row: int) -> QFrame:
        """Creates the layout for each button frame."""
        button_frame = QFrame()
        button_frame.setObjectName("buttonConfigFrame")
        button_frame.setFrameStyle(QFrame.Shape.Panel.value | QFrame.Shadow.Raised.value)
        frame_layout = QHBoxLayout(button_frame)

        # Header with button index
        the_layout = QVBoxLayout()
        frame_layout.addLayout(the_layout)

        header_layout = QHBoxLayout()
        direction = get_direction(row)
        header_label = QLabel(f" {direction} ")
        header_label.setObjectName("buttonConfigFrameHeader")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setFixedSize(40, 40)
        header_layout.addStretch()
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Add reset button for this frame
        reset_button = QPushButton()
        reset_button.setToolTip("Reset")
        reset_button.setIcon(get_icon("restart", is_inverted=True))
        reset_button.setFixedSize(24, 20)
        reset_button.setObjectName("buttonConfigSingleResetButton")
        reset_button.setProperty("button_index", index)
        reset_button.clicked.connect(
            lambda: reset_single_frame(reset_button, self.button_info, lambda: update_window_title(self.button_info, self)))

        reset_layout = QVBoxLayout()
        reset_layout.addStretch()
        reset_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignCenter)
        reset_layout.addStretch()

        the_layout.addLayout(header_layout)
        the_layout.addLayout(reset_layout)

        # Container for dropdowns and other content
        content_layout = QHBoxLayout()
        current_button_info = self.button_info[index]

        task_type_dropdown, exe_name_dropdown = self.create_dropdowns(current_button_info, index)
        content_layout.addLayout(create_texts_layout())
        content_layout.addLayout(create_dropdowns_layout(task_type_dropdown, exe_name_dropdown))

        frame_layout.addLayout(content_layout)
        return button_frame

    def create_dropdowns(self, current_button_info: dict, index: int) -> tuple[QComboBox, QComboBox]:
        """Creates dropdowns for task type and executable name."""
        task_type_dropdown = create_task_type_dropdown(self.task_types, current_button_info, index, self.on_task_type_changed)
        exe_name_dropdown = create_exe_name_dropdown(self.exe_names, current_button_info, index, self.on_exe_index_changed, self.on_exe_name_changed)
        return task_type_dropdown, exe_name_dropdown

    def reset_to_defaults(self) -> None:
        """Resets button configurations to defaults."""
        reset_to_defaults(self, self.button_info)

    def update_apps_info(self) -> None:
        """Updates the list of available executables from the JSON."""
        self.apps_info = JSONManager.load(CONFIG.INTERNAL_PROGRAM_NAME, "apps_info_cache.json", default={})
        self.exe_names = sorted([(exe_name, app_info["app_name"]) for exe_name, app_info in self.apps_info.items()])
        for exe_dropdown in self.findChildren(QComboBox):
            if not exe_dropdown.isEditable():
                continue
            current_text = exe_dropdown.currentText()
            exe_dropdown.blockSignals(True)
            exe_dropdown.clear()
            for exe_name, app_name in self.exe_names:
                display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
                exe_dropdown.addItem(display_text, exe_name)
            exe_dropdown.setCurrentText(current_text)
            exe_dropdown.blockSignals(False)

    def restore_values_from_model(self) -> None:
        """Restores values from the model for each button."""
        for button_frame in self.findChildren(QFrame, "buttonConfigFrame"):
            dropdowns = button_frame.findChildren(QComboBox)
            if not dropdowns:
                continue
            task_type_dropdown = dropdowns[0]
            exe_name_dropdown = dropdowns[1] if len(dropdowns) > 1 else None
            button_index = task_type_dropdown.property("button_index")
            current_button_info = self.button_info[button_index]
            task_type_dropdown.blockSignals(True)
            task_type_dropdown.setCurrentText(current_button_info["task_type"])
            task_type_dropdown.blockSignals(False)
            if exe_name_dropdown:
                exe_name_dropdown.blockSignals(True)
                if current_button_info["task_type"] == "show_any_window":
                    exe_name_dropdown.setCurrentText("")
                    exe_name_dropdown.setEnabled(False)
                else:
                    exe_name_dropdown.setEnabled(True)
                    exe_name = current_button_info["properties"].get("exe_name", "")
                    found_index = -1
                    for i in range(exe_name_dropdown.count()):
                        if exe_name_dropdown.itemData(i) == exe_name:
                            found_index = i
                            break
                    if found_index != -1:
                        exe_name_dropdown.setCurrentIndex(found_index)
                    else:
                        exe_name_dropdown.setCurrentText(exe_name)
                exe_name_dropdown.blockSignals(False)

    def closeEvent(self, event) -> None:
        """Handles closing the editor with unsaved changes."""
        if self.button_info.has_unsaved_changes:
            reply = QMessageBox.question(
                self, 'Unsaved Changes',
                'You have unsaved changes. Do you want to save before closing?',
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_changes()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                self.button_info.load_json()
                self.restore_values_from_model()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def showEvent(self, event) -> None:
        """Handles event when the editor is shown."""
        self.update_apps_info()
        super().showEvent(event)

    def on_task_type_changed(self, new_task_type: str) -> None:
        """Handles changes to task type in the dropdown."""
        sender = self.sender()
        button_index = sender.property("button_index")
        print(f"\nDEBUG: Task type changed to: {new_task_type}")
        print(f"DEBUG: Button index: {button_index}")

        try:
            button_frame = sender.parent().parent()
            if not button_frame:
                print("DEBUG: ERROR - Could not find button frame")
                return

            exe_dropdowns = [
                dropdown for dropdown in button_frame.findChildren(QComboBox)
                if (dropdown.property("button_index") == button_index and dropdown != sender)
            ]

            if not exe_dropdowns:
                print("DEBUG: ERROR - Could not find matching exe dropdown box")
                return

            exe_name_dropdown = exe_dropdowns[0]
            print(f"DEBUG: Found exe_name_dropdown with button_index: {exe_name_dropdown.property('button_index')}")
            print(f"DEBUG: Current enabled state: {exe_name_dropdown.isEnabled()}")
            print(f"DEBUG: Current text: '{exe_name_dropdown.currentText()}'")

            exe_name_dropdown.blockSignals(True)
            print("DEBUG: Clearing dropdown box")
            exe_name_dropdown.clear()

            if new_task_type == "show_any_window":
                print("DEBUG: Handling show_any_window")
                exe_name_dropdown.setEditable(True)
                exe_name_dropdown.setCurrentText("")
                exe_name_dropdown.setEnabled(False)
                print(f"DEBUG: After changes - enabled: {exe_name_dropdown.isEnabled()}, text: '{exe_name_dropdown.currentText()}'")

                updated_properties = {
                    "app_name": "",
                    "text_1": "",
                    "text_2": "",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": ""
                }
            else:
                print(f"DEBUG: Handling other type: {new_task_type}")
                exe_name_dropdown.setEnabled(True)
                print(f"DEBUG: Set enabled: {exe_name_dropdown.isEnabled()}")

                if new_task_type == "call_function":
                    print("DEBUG: Setting up call_function items")
                    from data.button_functions import ButtonFunctions
                    functions = ButtonFunctions().functions
                    exe_name_dropdown.setEditable(False)
                    for func_name, func_data in functions.items():
                        exe_name_dropdown.addItem(func_data['text_1'], func_name)
                    updated_properties = {
                        "function_name": exe_name_dropdown.currentData()
                    }
                else:
                    print("DEBUG: Setting up program items")
                    exe_name_dropdown.setEditable(True)
                    for exe_name, app_name in self.exe_names:
                        display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
                        exe_name_dropdown.addItem(display_text, exe_name)

                    if not self.button_info[button_index]["properties"].get("exe_name"):
                        for i in range(exe_name_dropdown.count()):
                            if exe_name_dropdown.itemData(i) == "explorer.exe":
                                exe_name_dropdown.setCurrentIndex(i)
                                break

                    current_exe = exe_name_dropdown.currentData() or ""
                    updated_properties = {
                        "app_name": "",
                        "app_icon_path": "",
                        "exe_name": current_exe,
                        "exe_path": "",
                        "window_title": "" if new_task_type == "show_program_window" else None
                    }

            print("DEBUG: Updating button configuration")
            self.button_info.update_button(button_index, {
                "task_type": new_task_type,
                "properties": updated_properties
            })

            print("DEBUG: Re-enabling signals")
            exe_name_dropdown.blockSignals(False)

            print(f"DEBUG: Final state - enabled: {exe_name_dropdown.isEnabled()}, text: '{exe_name_dropdown.currentText()}'")
            update_window_title(self.button_info, self)

        except Exception as e:
            logging.error(f"Failed to update task type: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update task type: {str(e)}")

    def on_exe_name_changed(self, new_exe_name: str, button_index: int) -> None:
        """Handles changes to the executable name in the dropdown."""
        try:
            current_config = self.button_info[button_index]
            task_type = current_config["task_type"]

            if task_type == "show_any_window":
                updated_properties = {
                    "app_name": "",
                    "text_1": "",
                    "text_2": "",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": new_exe_name
                }
            elif task_type == "show_program_window":
                updated_properties = {
                    "app_name": "",
                    "text_1": "",
                    "text_2": "",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": new_exe_name,
                    "exe_path": "",
                    "window_title": ""
                }
            elif task_type == "launch_program":
                updated_properties = {
                    "app_name": "",
                    "app_icon_path": "",
                    "exe_name": new_exe_name,
                    "exe_path": ""
                }
            elif task_type == "call_function":
                updated_properties = {
                    "function_name": ""  # call_function doesn't use exe_name
                }
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # Preserve existing values for properties that already exist
            for key, value in current_config.get("properties", {}).items():
                if key in updated_properties:
                    updated_properties[key] = value

            updated_properties["exe_name"] = new_exe_name

            # Update button with all properties
            self.button_info.update_button(button_index, {
                "properties": updated_properties
            })
            update_window_title(self.button_info, self)

        except Exception as e:
            logging.error(f"Failed to update exe name: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update exe name: {str(e)}")

    def on_exe_index_changed(self, idx: int, button_index: int, dropdown: QComboBox) -> None:
        """Handles changes to the executable index in the dropdown box."""
        value = dropdown.itemData(idx) or dropdown.currentText()
        self.on_exe_name_changed(value, button_index)

    def save_changes(self) -> None:
        """Saves the changes to the button configurations."""
        try:
            self.button_info.save_to_json()
            self.button_info.load_json()
            update_window_title(self.button_info, self)
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.close()
        except Exception as e:
            logging.error(f"Failed to save configuration: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    class NoScrollComboBox(QComboBox):
        def wheelEvent(self, event) -> None:
            """Disables scrolling in the dropdown box."""
            event.ignore()
