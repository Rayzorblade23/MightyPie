# button_info_editor.py

import logging

from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QComboBox, QFrame

from data.button_info import ButtonInfo
from data.config import CONFIG
from gui.elements.button_info_editor_components import ButtonFrame
from gui.elements.button_info_editor_dropdowns import ButtonDropdowns
from utils.button_info_editor_utils import (
    update_window_title, create_scroll_area, create_column, create_button_container
)

logging.basicConfig(level=logging.DEBUG)


class ButtonInfoEditor(QWidget):
    def __init__(self) -> None:
        """Initializes the ButtonInfoEditor with necessary setups."""
        super().__init__()
        self.button_info = ButtonInfo.get_instance()
        self.temp_config = TemporaryButtonConfig()  # Add temporary storage
        self.dropdowns = ButtonDropdowns(self)

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
        return ButtonFrame(index, row, self)

    def create_dropdowns(self, current_button_info: dict, index: int) -> tuple[QComboBox, QComboBox]:
        """Creates dropdowns for task type and value."""
        return self.dropdowns.create_dropdowns(current_button_info, index)

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
        """Updates the list of available executables."""
        self.dropdowns.update_apps_info()

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

        logging.debug(f"on_task_type_changed called with new_task_type: {new_task_type}, button_index: {button_index}")

        try:
            # Convert display text back to internal task type format
            internal_task_type = new_task_type.lower().replace(' ', '_')
            logging.debug(f"Converted to internal_task_type: {internal_task_type}")

            # Get default properties from ButtonInfo
            default_properties = ButtonInfo.get_default_properties(internal_task_type)

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

            # Update temp config with correct task type and default properties
            self.temp_config.update_button(button_index, {
                "task_type": internal_task_type,
                "properties": default_properties
            })
            logging.debug(f"Updated temp config with defaults: {self.temp_config._temp_changes.get(button_index)}")

            # Update UI based on task type
            if internal_task_type == "show_any_window":
                value_dropdown.setEditable(True)
                value_dropdown.setCurrentText("")
                value_dropdown.setEnabled(False)

            elif internal_task_type in ["show_program_window", "launch_program"]:
                value_dropdown.setEditable(True)
                value_dropdown.setEnabled(True)
                for exe_name, app_name in self.dropdowns.exe_names:
                    display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
                    value_dropdown.addItem(display_text, exe_name)
                # Set explorer.exe as default
                for i in range(value_dropdown.count()):
                    if value_dropdown.itemData(i) == "explorer.exe":
                        value_dropdown.setCurrentIndex(i)
                        break

            elif internal_task_type == "call_function":
                from data.button_functions import ButtonFunctions
                functions = ButtonFunctions().functions
                value_dropdown.setEditable(False)
                value_dropdown.setEnabled(True)
                for func_name, func_data in functions.items():
                    value_dropdown.addItem(func_data['text_1'], func_name)
                # Set first function as default
                if value_dropdown.count() > 0:
                    first_function = value_dropdown.itemData(0)
                    self.temp_config.update_button(button_index, {
                        "task_type": internal_task_type,
                        "properties": {"function_name": first_function}
                    })

            value_dropdown.blockSignals(False)
            logging.debug(f"Final temp config state: {self.temp_config._temp_changes.get(button_index)}")
            update_window_title(self.temp_config, self)

        except Exception as e:
            logging.error(f"Failed to update task type: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update task type: {str(e)}")

    def on_value_changed(self, new_value: str, button_index: int) -> None:
        """Handles changes to the value (exe name or function name) in the dropdown."""
        logging.debug(f"on_value_changed called with new_value: {new_value}, button_index: {button_index}")
        try:
            # Get the current config from temp_config first, fall back to button_info
            current_config = self.temp_config._temp_changes.get(button_index) or self.button_info[button_index]
            task_type = current_config["task_type"]
            logging.debug(f"Current task_type from temp_config: {task_type}")
            logging.debug(f"Current temp config state: {self.temp_config._temp_changes.get(button_index)}")

            # Keep existing properties and update only relevant field
            current_properties = current_config.get("properties", {}).copy()

            if task_type == "call_function":
                from data.button_functions import ButtonFunctions
                functions = ButtonFunctions().functions
                if new_value in functions:
                    current_properties["function_name"] = new_value
                else:
                    first_function = next(iter(functions.keys()))
                    current_properties["function_name"] = first_function

            elif task_type in ["show_program_window", "launch_program", "show_any_window"]:
                current_properties["exe_name"] = new_value

            self.temp_config.update_button(button_index, {
                "task_type": task_type,
                "properties": current_properties
            })

            logging.debug(f"Updated temp config: {self.temp_config._temp_changes.get(button_index)}")
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
        logging.debug(f"TemporaryButtonConfig.update_button called with index: {index}, changes: {changes}")
        if index not in self._temp_changes:
            self._temp_changes[index] = {"task_type": "", "properties": {}}

        # Update task_type if provided
        if "task_type" in changes:
            self._temp_changes[index]["task_type"] = changes["task_type"]

        # Update or merge properties if provided
        if "properties" in changes:
            self._temp_changes[index]["properties"].update(changes["properties"])

        logging.debug(f"Updated temp changes for index {index}: {self._temp_changes[index]}")

    def apply_changes(self, button_info: ButtonInfo) -> None:
        for index, changes in self._temp_changes.items():
            button_info.update_button(index, changes)
        self.clear()

    def clear(self) -> None:
        self._temp_changes.clear()

    def has_changes(self) -> bool:
        return bool(self._temp_changes)
