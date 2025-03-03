# button_info_editor.py

import logging

from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QComboBox, QFrame, QApplication

from src.data.button_config_manager import ButtonConfigManager
from src.data.config import CONFIG
from src.gui.elements.button_info_editor_components import ButtonFrame
from src.gui.elements.button_info_editor_dropdowns import ButtonDropdowns
from src.utils.button_info_editor_utils import (
    update_window_title, create_scroll_area, create_column, create_button_container
)

logger = logging.getLogger(__name__)


class ButtonInfoEditor(QWidget):
    def __init__(self) -> None:
        """Initializes the ButtonInfoEditor with necessary setups."""
        super().__init__()
        self.config_manager = ButtonConfigManager()
        self.button_info = self.config_manager.button_info
        self.dropdowns = ButtonDropdowns(self)

        self.init_ui()

    def init_ui(self) -> None:
        """Sets up the user interface components."""
        # Get the available screen geometry
        screen = QApplication.primaryScreen().availableGeometry()

        self.setWindowTitle('Button Info Editor')
        # Calculate dimensions based on screen size (e.g., 80% of available space)
        width = min(1800, int(screen.width() * 0.8))
        height = min(860, int(screen.height() * 0.8))

        self.setGeometry(50, 50, width, height)

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
                self.config_manager.reset_all()
                self.restore_values_from_model()
                update_window_title(self.config_manager, self)
            except Exception as e:
                logger.error(f"Error in reset_to_defaults: {str(e)}")
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

            # Get current config from config manager
            current_button_info = self.config_manager.get_current_config(button_index)

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
        if self.config_manager.has_unsaved_changes():
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
                self.config_manager.discard_changes()
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
        """Handles changes to the task type in the dropdown."""
        sender = self.sender()
        button_index = sender.property("button_index")

        try:
            internal_task_type = new_task_type.lower().replace(' ', '_')
            self.config_manager.update_task_type(button_index, internal_task_type)

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
            self._update_value_dropdown(value_dropdown, internal_task_type)
            update_window_title(self.config_manager, self)

        except Exception as e:
            logger.error(f"Failed to update task type: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update task type: {str(e)}")

    # Add helper method
    def _update_value_dropdown(self, dropdown: QComboBox, task_type: str) -> None:
        """Updates the value dropdown based on the selected task type."""
        dropdown.blockSignals(True)
        dropdown.clear()

        if task_type == "show_any_window":
            dropdown.setEditable(True)
            dropdown.setCurrentText("")
            dropdown.setEnabled(False)
        elif task_type in ["show_program_window", "launch_program"]:
            dropdown.setEditable(True)
            dropdown.setEnabled(True)
            for exe_name, app_name in self.dropdowns.exe_names:
                display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
                dropdown.addItem(display_text, exe_name)
            # Set explorer.exe as default
            for i in range(dropdown.count()):
                if dropdown.itemData(i) == "explorer.exe":
                    dropdown.setCurrentIndex(i)
                    break
        elif task_type == "call_function":
            from src.data.button_functions import ButtonFunctions
            functions = ButtonFunctions().functions
            dropdown.setEditable(False)
            dropdown.setEnabled(True)
            for func_name, func_data in functions.items():
                dropdown.addItem(func_data['text_1'], func_name)

        dropdown.blockSignals(False)

    def on_value_changed(self, new_value: str, button_index: int) -> None:
        """Handles changes to the value (exe name or function name) in the dropdown."""
        logger.debug(f"on_value_changed called with new_value: {new_value}, button_index: {button_index}")
        try:
            self.config_manager.update_value(button_index, new_value)
            update_window_title(self.config_manager, self)
        except Exception as e:
            logger.error(f"Failed to update value: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update value: {str(e)}")

    def on_value_index_changed(self, idx: int, button_index: int, dropdown: QComboBox) -> None:
        """Handles changes to the value index in the dropdown box."""
        value = dropdown.itemData(idx) or dropdown.currentText()
        self.on_value_changed(value, button_index)

    def save_changes(self) -> None:
        """Saves the changes to the button configurations."""
        try:
            self.config_manager.save_changes()
            update_window_title(self.config_manager, self)
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.close()
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    class NoScrollComboBox(QComboBox):
        def wheelEvent(self, event) -> None:
            """Disables scrolling in the dropdown box."""
            event.ignore()
