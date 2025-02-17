import logging
from functools import partial

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QScrollArea, \
    QPushButton, QFrame

from data.button_info import ButtonInfo
from data.config import CONFIG
from gui.buttons.pie_button import BUTTON_TYPES
from utils.file_handling_utils import get_resource_path
from utils.icon_utils import get_icon
from utils.json_utils import JSONManager

logging.basicConfig(level=logging.DEBUG)


class ButtonInfoEditor(QWidget):
    def __init__(self):
        print("Starting ButtonInfoEditor init")  # Debug
        print(f"Current thread: {QThread.currentThread()}")  # Debug
        super().__init__()
        self.button_info = ButtonInfo.get_instance()
        print(f"ButtonInfo instance: {id(self.button_info)}")  # Debug

        # Available options for dropdowns
        self.task_types = list(BUTTON_TYPES.keys())


        self.apps_info = JSONManager.load(CONFIG.INTERNAL_PROGRAM_NAME, "apps_info_cache.json", default={})

        # Extract exe names (keys in the JSON)
        self.exe_names = sorted([(exe_name, app_info["app_name"]) for exe_name, app_info in self.apps_info.items()])

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Button Info Editor')
        self.setGeometry(100, 100, 1500, 860)

        # Create the main layout
        main_layout = QVBoxLayout(self)

        # Create scroll area
        scroll, scroll_layout = self.create_scroll_area()
        main_layout.addWidget(scroll)

        # Calculate number of columns needed
        num_columns = CONFIG.INTERNAL_NUM_PIE_MENUS_PRIMARY + CONFIG.INTERNAL_NUM_PIE_MENUS_SECONDARY
        buttons_per_column = CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU

        # Create columns
        for col in range(num_columns):
            column_widget, column_layout = self.create_column(col)
            scroll_layout.addWidget(column_widget)

        # Create button container
        button_container = self.create_button_container()
        main_layout.addLayout(button_container)

    def create_scroll_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        return scroll, scroll_layout

    def create_column(self, col):
        column_widget = QWidget()
        column_layout = QVBoxLayout(column_widget)

        # Add column title
        title_label = QLabel(f"Pie Menu {col + 1}")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        column_layout.addWidget(title_label)

        # Add vertical line separator before each column except the first
        if col > 0:
            line = QFrame()
            line.setFrameStyle(QFrame.Shape.VLine.value)
            line.setLineWidth(1)
            column_layout.addWidget(line)

        # Add buttons to this column
        for row in range(CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU):
            index = row + (col * CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU)
            button_frame = self.create_button_frame(index, row)
            column_layout.addWidget(button_frame)

        column_layout.addStretch()
        return column_widget, column_layout

    def create_button_frame(self, index, row):
        button_frame = QFrame()
        button_frame.setObjectName("buttonConfigFrame")
        button_frame.setFrameStyle(QFrame.Shape.Panel.value | QFrame.Shadow.Raised.value)
        frame_layout = QHBoxLayout(button_frame)

        # Header with button index
        the_layout = QVBoxLayout()
        frame_layout.addLayout(the_layout)

        header_layout = QHBoxLayout()
        direction = self.get_direction(row)
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
        reset_button.clicked.connect(self.reset_single_frame)

        reset_layout = QVBoxLayout()
        reset_layout.addStretch()
        reset_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignCenter)
        reset_layout.addStretch()

        the_layout.addLayout(header_layout)
        the_layout.addLayout(reset_layout)

        # Container for dropdowns and other content
        content_layout = QHBoxLayout()
        current_task = self.button_info[index]

        task_type_combo, exe_name_combo = self.create_dropdowns(current_task, index)
        content_layout.addLayout(self.create_texts_layout())
        content_layout.addLayout(self.create_dropdowns_layout(task_type_combo, exe_name_combo))

        frame_layout.addLayout(content_layout)
        return button_frame

    def create_texts_layout(self):
        texts_layout = QVBoxLayout()
        texts_layout.addWidget(QLabel("Task Type:"))
        texts_layout.addWidget(QLabel("Program:"))
        return texts_layout

    def create_dropdowns_layout(self, task_type_combo, exe_name_combo):
        dropdowns_layout = QVBoxLayout()
        dropdowns_layout.addWidget(task_type_combo)
        dropdowns_layout.addWidget(exe_name_combo)
        return dropdowns_layout

    def create_dropdowns(self, current_task, index):
        task_type_combo = self.create_task_type_combo(current_task, index)
        exe_name_combo = self.create_exe_name_combo(current_task, index)
        return task_type_combo, exe_name_combo

    def create_task_type_combo(self, current_task, index):
        task_type_combo = self.NoScrollComboBox()
        # Format task types for display
        for task_type in self.task_types:
            display_text = task_type.replace('_', ' ').title()
            task_type_combo.addItem(display_text, task_type)
        # Find and set current item
        current_index = self.task_types.index(current_task["task_type"])
        task_type_combo.setCurrentIndex(current_index)
        task_type_combo.setProperty("button_index", index)
        task_type_combo.currentTextChanged.connect(lambda text: self.on_task_type_changed(self.task_types[task_type_combo.currentIndex()]))
        return task_type_combo

    def create_exe_name_combo(self, current_task, index):
        exe_name_combo = self.NoScrollComboBox()
        exe_name_combo.setProperty("button_index", index)

        # Block signals while setting up
        exe_name_combo.blockSignals(True)

        if current_task["task_type"] == "show_any_window":
            # For show_any_window, set empty and disabled first
            exe_name_combo.setEnabled(False)
            exe_name_combo.setEditable(True)
            exe_name_combo.clear()
            exe_name_combo.setCurrentText("")
        elif current_task["task_type"] == "call_function":
            # Handle call_function
            from data.button_functions import ButtonFunctions
            functions = ButtonFunctions().functions
            exe_name_combo.setEditable(False)
            exe_name_combo.setEnabled(True)
            for func_name, func_data in functions.items():
                exe_name_combo.addItem(func_data['text_1'], func_name)

            # Set current function if exists
            current_function = current_task["properties"].get("function_name", "")
            if current_function:
                for i in range(exe_name_combo.count()):
                    if exe_name_combo.itemData(i) == current_function:
                        exe_name_combo.setCurrentIndex(i)
                        break
        else:
            # Handle other task types
            exe_name_combo.setEditable(True)
            exe_name_combo.setEnabled(True)
            for exe_name, app_name in self.exe_names:
                display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
                exe_name_combo.addItem(display_text, exe_name)

            current_exe_name = current_task["properties"].get("exe_name", "")
            if current_exe_name:
                # Set existing value
                for i in range(exe_name_combo.count()):
                    if exe_name_combo.itemData(i) == current_exe_name:
                        exe_name_combo.setCurrentIndex(i)
                        break
            else:
                # Set explorer.exe as default
                for i in range(exe_name_combo.count()):
                    if exe_name_combo.itemData(i) == "explorer.exe":
                        exe_name_combo.setCurrentIndex(i)
                        break

        # Connect signals after setup
        exe_name_combo.currentIndexChanged.connect(
            partial(self.on_exe_index_changed, button_index=index, combo=exe_name_combo)
        )
        exe_name_combo.editTextChanged.connect(lambda text, idx=index: self.on_exe_name_changed(text, idx))

        # Re-enable signals
        exe_name_combo.blockSignals(False)
        return exe_name_combo
    def create_button_container(self):
        button_container = QHBoxLayout()
        reset_button = QPushButton("Reset to Defaults")
        reset_button.setObjectName("buttonConfigButton")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_container.addWidget(reset_button)

        save_button = QPushButton("Save Changes")
        save_button.setObjectName("buttonConfigButton")
        save_button.clicked.connect(self.save_changes)
        button_container.addWidget(save_button)
        return button_container

    def get_direction(self, row):
        directions = ["⭡", "⭧", "⭢", "⭨", "⭣", "⭩", "⭠", "⭦"]
        return directions[row] if row < len(directions) else ""

    def reset_single_frame(self):
        sender = self.sender()
        button_index = sender.property("button_index")
        if button_index is None:
            return

        button_frame = sender.parent()
        task_type_combo = button_frame.findChild(QComboBox)
        if task_type_combo:
            task_type_combo.setCurrentText("show_any_window")
            exe_name_combo = button_frame.findChild(QComboBox, None)
            if exe_name_combo and exe_name_combo != task_type_combo:
                exe_name_combo.setCurrentText("")
                exe_name_combo.setEnabled(False)
            self.button_info.update_button(button_index, {
                "task_type": "show_any_window",
                "properties": {"exe_name": ""}
            })
        self.update_window_title()

    def reset_to_defaults(self):
        reply = QMessageBox.question(
            self, "Reset Confirmation",
            "Are you sure you want to reset all settings to default?\nYou can still discard the changes afterwards.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for button_frame in self.findChildren(QFrame, "buttonConfigFrame"):
                task_type_combo = button_frame.findChild(QComboBox)
                if task_type_combo:
                    button_index = task_type_combo.property("button_index")
                    task_type_combo.setCurrentText("show_any_window")
                    exe_name_combo = button_frame.findChild(QComboBox, None)
                    if exe_name_combo and exe_name_combo != task_type_combo:
                        exe_name_combo.setCurrentText("")
                        exe_name_combo.setEnabled(False)
                    self.button_info.update_button(button_index, {
                        "task_type": "show_any_window",
                        "properties": {"exe_name": ""}
                    })
            self.update_window_title()

    def update_apps_info(self):
        self.apps_info = JSONManager.load(CONFIG.INTERNAL_PROGRAM_NAME, "apps_info_cache.json", default={})
        self.exe_names = sorted([(exe_name, app_info["app_name"]) for exe_name, app_info in self.apps_info.items()])
        for exe_combo in self.findChildren(QComboBox):
            if not exe_combo.isEditable():
                continue
            current_text = exe_combo.currentText()
            exe_combo.blockSignals(True)
            exe_combo.clear()
            for exe_name, app_name in self.exe_names:
                display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
                exe_combo.addItem(display_text, exe_name)
            exe_combo.setCurrentText(current_text)
            exe_combo.blockSignals(False)

    def restore_values_from_model(self):
        for button_frame in self.findChildren(QFrame, "buttonConfigFrame"):
            combos = button_frame.findChildren(QComboBox)
            if not combos:
                continue
            task_type_combo = combos[0]
            exe_name_combo = combos[1] if len(combos) > 1 else None
            button_index = task_type_combo.property("button_index")
            current_task = self.button_info[button_index]
            task_type_combo.blockSignals(True)
            task_type_combo.setCurrentText(current_task["task_type"])
            task_type_combo.blockSignals(False)
            if exe_name_combo:
                exe_name_combo.blockSignals(True)
                if current_task["task_type"] == "show_any_window":
                    exe_name_combo.setCurrentText("")
                    exe_name_combo.setEnabled(False)
                else:
                    exe_name_combo.setEnabled(True)
                    exe_name = current_task["properties"].get("exe_name", "")
                    found_index = -1
                    for i in range(exe_name_combo.count()):
                        if exe_name_combo.itemData(i) == exe_name:
                            found_index = i
                            break
                    if found_index != -1:
                        exe_name_combo.setCurrentIndex(found_index)
                    else:
                        exe_name_combo.setCurrentText(exe_name)
                exe_name_combo.blockSignals(False)

    def closeEvent(self, event):
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

    def showEvent(self, event):
        self.update_apps_info()
        super().showEvent(event)

    def on_task_type_changed(self, new_task_type):
        sender = self.sender()
        button_index = sender.property("button_index")
        print(f"\nDEBUG: Task type changed to: {new_task_type}")
        print(f"DEBUG: Button index: {button_index}")

        try:
            # Get the grandparent (button frame)
            button_frame = sender.parent().parent()
            if not button_frame:
                print("DEBUG: ERROR - Could not find button frame")
                return

            # Find all combo boxes in this frame that have the same button_index
            exe_combos = [
                combo for combo in button_frame.findChildren(QComboBox)
                if (combo.property("button_index") == button_index and combo != sender)
            ]

            if not exe_combos:
                print("DEBUG: ERROR - Could not find matching exe combo box")
                return

            exe_name_combo = exe_combos[0]
            print(f"DEBUG: Found exe_name_combo with button_index: {exe_name_combo.property('button_index')}")
            print(f"DEBUG: Current enabled state: {exe_name_combo.isEnabled()}")
            print(f"DEBUG: Current text: '{exe_name_combo.currentText()}'")

            # Block signals during updates
            exe_name_combo.blockSignals(True)

            print("DEBUG: Clearing combo box")
            exe_name_combo.clear()

            if new_task_type == "show_any_window":
                print("DEBUG: Handling show_any_window")
                exe_name_combo.setEditable(True)
                exe_name_combo.setCurrentText("")
                exe_name_combo.setEnabled(False)
                print(f"DEBUG: After changes - enabled: {exe_name_combo.isEnabled()}, text: '{exe_name_combo.currentText()}'")

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
                # Enable the combo box first
                exe_name_combo.setEnabled(True)
                print(f"DEBUG: Set enabled: {exe_name_combo.isEnabled()}")

                if new_task_type == "call_function":
                    print("DEBUG: Setting up call_function items")
                    from data.button_functions import ButtonFunctions
                    functions = ButtonFunctions().functions
                    exe_name_combo.setEditable(False)
                    for func_name, func_data in functions.items():
                        exe_name_combo.addItem(func_data['text_1'], func_name)
                    updated_properties = {
                        "function_name": exe_name_combo.currentData()
                    }
                else:
                    print("DEBUG: Setting up program items")
                    exe_name_combo.setEditable(True)
                    for exe_name, app_name in self.exe_names:
                        display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
                        exe_name_combo.addItem(display_text, exe_name)

                    if not self.button_info[button_index]["properties"].get("exe_name"):
                        for i in range(exe_name_combo.count()):
                            if exe_name_combo.itemData(i) == "explorer.exe":
                                exe_name_combo.setCurrentIndex(i)
                                break

                    current_exe = exe_name_combo.currentData() or ""
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
            exe_name_combo.blockSignals(False)

            print(f"DEBUG: Final state - enabled: {exe_name_combo.isEnabled()}, text: '{exe_name_combo.currentText()}'")
            self.update_window_title()

        except Exception as e:
            logging.error(f"Failed to update task type: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update task type: {str(e)}")
            
    def on_exe_name_changed(self, new_exe_name, button_index):
        try:
            # Get the current button configuration
            current_config = self.button_info[button_index]
            task_type = current_config["task_type"]

            # Initialize properties based on task_type
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

            # Update the exe_name
            updated_properties["exe_name"] = new_exe_name

            # Update button with all properties
            self.button_info.update_button(button_index, {
                "properties": updated_properties
            })
            self.update_window_title()

        except Exception as e:
            logging.error(f"Failed to update exe name: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update exe name: {str(e)}")

    def on_exe_index_changed(self, idx, button_index, combo):
        value = combo.itemData(idx) or combo.currentText()
        self.on_exe_name_changed(value, button_index)

    def update_window_title(self):
        title = "Button Info Editor"
        if self.button_info.has_unsaved_changes:
            title += " *"
        self.setWindowTitle(title)

    def save_changes(self):
        try:
            self.button_info.save_to_json()
            self.button_info.load_json()
            self.update_window_title()
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.close()
        except Exception as e:
            logging.error(f"Failed to save configuration: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    class NoScrollComboBox(QComboBox):
        def wheelEvent(self, event):
            event.ignore()


def main():
    import sys
    app = QApplication(sys.argv)
    with open(get_resource_path("../../style.qss"), "r") as file:
        qss_template = file.read()
    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", CONFIG.ACCENT_COLOR_MUTED)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))
    app.setStyleSheet(qss)
    editor = ButtonInfoEditor()
    editor.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
