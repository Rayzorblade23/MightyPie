# button_info_editor.py

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFrame, QPushButton, QLabel

from data.button_info import ButtonInfo
from data.config import CONFIG
from gui.buttons.pie_button import BUTTON_TYPES
from utils.button_info_editor_utils import (
    update_window_title, create_scroll_area, create_column, get_direction, create_button_container,
    create_task_type_dropdown, create_value_dropdown, create_texts_layout, create_dropdowns_layout, reset_single_frame
)
from utils.icon_utils import get_icon
from utils.json_utils import JSONManager

logging.basicConfig(level=logging.DEBUG)


class ButtonInfoEditor(QWidget):
    def __init__(self) -> None:
        """Initializes the ButtonInfoEditor with necessary setups."""
        super().__init__()
        self.button_info = ButtonInfo.get_instance()
        self.temp_config = TemporaryButtonConfig()  # Add temporary storage

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
            lambda: reset_single_frame(
                sender=reset_button,
                button_info=self.button_info,
                temp_config=self.temp_config,  # Pass temp_config here
                update_window_title=lambda: update_window_title(self.temp_config, self)
            )
        )
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
        """Creates dropdowns for task type and value (exe name or function name)."""
        task_type_dropdown = create_task_type_dropdown(self.task_types, current_button_info, index, self.on_task_type_changed)
        value_dropdown = create_value_dropdown(self.exe_names, current_button_info, index, self.on_value_index_changed,
                                               self.on_value_changed)
        return task_type_dropdown, value_dropdown

    def reset_to_defaults(self) -> None:
        """Resets all button configurations to defaults in temporary storage."""
        reply = QMessageBox.question(
            self, "Reset Confirmation",
            "Are you sure you want to reset all settings to default?\nYou can still discard the changes afterwards.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Reset all 40 buttons regardless of UI visibility
                for button_index in range(40):
                    self.temp_config.update_button(button_index, {
                        "task_type": "show_any_window",
                        "properties": {
                            "app_name": "",
                            "app_icon_path": "",
                            "window_title": "",
                            "window_handle": -1,
                            "exe_name": "",
                            "exe_path": ""
                        }
                    })

                # Update visible UI elements
                self.restore_values_from_model()
                update_window_title(self.temp_config, self)

            except Exception as e:
                logging.error(f"Error in reset_to_defaults: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to reset configuration: {str(e)}")

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

            # Check temp_config first, fall back to button_info if no changes
            if button_index in self.temp_config._temp_changes:
                current_button_info = self.temp_config._temp_changes[button_index]
            else:
                current_button_info = self.button_info[button_index]

            # Update task type dropdown
            task_type_dropdown.blockSignals(True)
            if "task_type" in current_button_info:
                display_text = current_button_info["task_type"].replace('_', ' ').title()
                task_type_dropdown.setCurrentText(display_text)
            task_type_dropdown.blockSignals(False)

            # Update exe name dropdown
            if exe_name_dropdown:
                exe_name_dropdown.blockSignals(True)
                if current_button_info.get("task_type") == "show_any_window":
                    exe_name_dropdown.setCurrentText("")
                    exe_name_dropdown.setEnabled(False)
                else:
                    exe_name_dropdown.setEnabled(True)
                    if "properties" in current_button_info:
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
        if self.temp_config.has_changes():  # Check temp_config instead
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
                self.temp_config.clear()  # Clear temp changes
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

        try:
            button_frame = sender.parent().parent()
            if not button_frame:
                return

            value_dropdowns = [
                dropdown for dropdown in button_frame.findChildren(QComboBox)
                if (dropdown.property("button_index") == button_index and dropdown != sender)
            ]

            if not value_dropdowns:
                return

            value_dropdown = value_dropdowns[0]
            value_dropdown.blockSignals(True)
            value_dropdown.clear()

            # Update UI based on task type
            if new_task_type == "show_any_window":
                value_dropdown.setEditable(True)
                value_dropdown.setCurrentText("")
                value_dropdown.setEnabled(False)

            elif new_task_type in ["show_program_window", "launch_program"]:
                value_dropdown.setEditable(True)
                value_dropdown.setEnabled(True)
                for exe_name, app_name in self.exe_names:
                    display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
                    value_dropdown.addItem(display_text, exe_name)

            elif new_task_type == "call_function":
                from data.button_functions import ButtonFunctions
                functions = ButtonFunctions().functions
                value_dropdown.setEditable(False)
                value_dropdown.setEnabled(True)
                for func_name, func_data in functions.items():
                    value_dropdown.addItem(func_data['text_1'], func_name)
                # Set first function as default
                if value_dropdown.count() > 0:
                    first_function = value_dropdown.itemData(0)
                    self.temp_config.update_button(button_index, {  # Use temp_config
                        "task_type": new_task_type,
                        "properties": {"function_name": first_function}
                    })
                    value_dropdown.setCurrentIndex(0)
                    value_dropdown.blockSignals(False)
                    update_window_title(self.temp_config, self)  # Pass temp_config
                    return

            # Use temp_config for other updates
            self.temp_config.update_button(button_index, {"task_type": new_task_type})
            update_window_title(self.temp_config, self)

            # Set default values after initialization
            if new_task_type in ["show_program_window", "launch_program"]:
                for i in range(value_dropdown.count()):
                    if value_dropdown.itemData(i) == "explorer.exe":
                        value_dropdown.setCurrentIndex(i)
                        break

            value_dropdown.blockSignals(False)

        except Exception as e:
            logging.error(f"Failed to update task type: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update task type: {str(e)}")

    def on_value_changed(self, new_value: str, button_index: int) -> None:
        """Handles changes to the value (exe name or function name) in the dropdown."""
        try:
            current_config = self.button_info[button_index]
            task_type = current_config["task_type"]

            # Let update_button handle property initialization based on task type
            updated_properties = {}

            if task_type == "call_function":
                # Ensure we have a valid function
                from data.button_functions import ButtonFunctions
                functions = ButtonFunctions().functions
                if new_value in functions:
                    updated_properties["function_name"] = new_value
                else:
                    # Set to first available function if invalid
                    first_function = next(iter(functions.keys()))
                    updated_properties["function_name"] = first_function

            elif task_type in ["show_program_window", "launch_program"]:
                updated_properties["exe_name"] = new_value

            self.temp_config.update_button(button_index, {  # Use temp_config
                "properties": updated_properties
            })
            update_window_title(self.temp_config, self)

        except Exception as e:
            logging.error(f"Failed to update value: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update value: {str(e)}")

    def on_value_index_changed(self, idx: int, button_index: int, dropdown: QComboBox) -> None:
        """Handles changes to the value index in the dropdown box."""
        value = dropdown.itemData(idx) or dropdown.currentText()
        self.on_value_changed(value, button_index)

    def save_changes(self) -> None:
        """Saves the changes to the button configurations."""
        try:
            # Apply temporary changes to the button_info instance
            self.temp_config.apply_changes(self.button_info)

            # Sort the button configuration by index
            sorted_config = dict(sorted(self.button_info.button_info_dict.items(), key=lambda x: int(x[0])))
            self.button_info.button_info_dict = sorted_config

            # Save the updated configuration to JSON
            self.button_info.save_to_json()

            # Clear temporary storage
            self.temp_config.clear()

            # Update window title
            update_window_title(self.temp_config, self)

            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.close()
        except Exception as e:
            logging.error(f"Failed to save configuration: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    class NoScrollComboBox(QComboBox):
        def wheelEvent(self, event) -> None:
            """Disables scrolling in the dropdown box."""
            event.ignore()


class TemporaryButtonConfig:
    """Temporarily stores button configuration changes until saved."""

    def __init__(self):
        self._temp_changes = {}

    def update_button(self, index: int, changes: dict) -> None:
        if index not in self._temp_changes:
            self._temp_changes[index] = {}
        self._temp_changes[index].update(changes)

    def apply_changes(self, button_info: ButtonInfo) -> None:
        for index, changes in self._temp_changes.items():
            button_info.update_button(index, changes)
        self.clear()

    def clear(self) -> None:
        self._temp_changes.clear()

    def has_changes(self) -> bool:
        return bool(self._temp_changes)
