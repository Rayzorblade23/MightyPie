# button_info_editor.py

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QScrollArea, \
    QPushButton, QFrame

from button_info import ButtonInfo
from config import CONFIG
from functions.file_handling_functions import get_resource_path
from functions.icon_functions_and_paths import get_icon
from json_utils import JSONManager


class ButtonInfoEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.button_info = ButtonInfo()

        # Available options for dropdowns
        self.task_types = ["program_window_fixed", "program_window_any"]

        # Load data from apps_info_cache.json
        apps_info = JSONManager.load(CONFIG._PROGRAM_NAME, "apps_info_cache.json", default={})

        # Extract exe names (keys in the JSON)
        self.exe_names = sorted([(exe_name, app_info["app_name"]) for exe_name, app_info in apps_info.items()])

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Button Info Editor')
        self.setGeometry(100, 100, 1000, 860)

        # Create the main layout
        main_layout = QVBoxLayout(self)

        # Create scroll area
        scroll, scroll_layout = self.create_scroll_area()
        main_layout.addWidget(scroll)

        # Calculate number of columns needed
        num_columns = CONFIG._NUM_PIE_TASK_SWITCHERS
        buttons_per_column = CONFIG._MAX_BUTTONS

        # Create columns
        for col in range(num_columns):
            # Create a column container
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
                scroll_layout.addWidget(line)

            # Add buttons to this column
            for row in range(buttons_per_column):
                # Calculate index to increment top-to-bottom
                index = row + (col * buttons_per_column)

                button_frame = QFrame()
                button_frame.setObjectName("buttonConfigFrame")
                button_frame.setFrameStyle(QFrame.Shape.Panel.value | QFrame.Shadow.Raised.value)
                frame_layout = QHBoxLayout(button_frame)

                # Header with button index
                the_layout = QVBoxLayout()
                frame_layout.addLayout(the_layout)

                header_layout = QHBoxLayout()

                direction = ""

                if row == 0:
                    direction = "⭡"  # Up
                elif row == 1:
                    direction = "⭧"  # Up-Right
                elif row == 2:
                    direction = "⭢"  # Right
                elif row == 3:
                    direction = "⭨"  # Down-Right
                elif row == 4:
                    direction = "⭣"  # Down
                elif row == 5:
                    direction = "⭩"  # Down-Left
                elif row == 6:
                    direction = "⭠"  # Left
                elif row == 7:
                    direction = "⭦"  # Up-Left

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
                reset_layout.addStretch()  # Push to center vertically
                reset_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignCenter)
                reset_layout.addStretch()  # Push to center vertically

                the_layout.addLayout(header_layout)
                the_layout.addLayout(reset_layout)

                # Container for dropdowns and other content
                content_layout = QHBoxLayout()  # Vertical layout for dropdowns

                current_task = self.button_info[index]

                class NoScrollComboBox(QComboBox):
                    """QComboBox that ignores mouse wheel scrolling."""

                    def wheelEvent(self, event):
                        event.ignore()  # Prevents the wheel from changing the selection

                # Task type selector
                texts_layout = QVBoxLayout()
                dropdowns_layout = QVBoxLayout()
                task_type_combo = NoScrollComboBox()
                task_type_combo.addItems(self.task_types)
                task_type_combo.setCurrentText(current_task["task_type"])

                texts_layout.addWidget(QLabel("Task Type:"))
                texts_layout.addWidget(QLabel("Program:"))

                dropdowns_layout.addWidget(task_type_combo)
                content_layout.addLayout(texts_layout)

                # Exe name selector
                exe_name_combo = NoScrollComboBox()

                # Add items to combo box with display text and actual data
                for exe_name, app_name in self.exe_names:
                    # print(f"App Name: {app_name} and exe: {exe_name}")
                    if not app_name.strip():  # If app_name is empty
                        display_text = f"({exe_name})"
                    else:  # If app_name is empty, just show exe_name in parentheses
                        display_text = f"{app_name}"

                    exe_name_combo.addItem(display_text, exe_name)

                # Find the current exe_name in the button_info
                current_exe_name = current_task["properties"]["exe_name"]

                # Set the current index based on the actual exe_name (stored in userData)
                for i in range(exe_name_combo.count()):
                    if exe_name_combo.itemData(i) == current_exe_name:
                        exe_name_combo.setCurrentIndex(i)
                        break

                # Connect signal using lambda to get both display text and data
                def create_handler(button_index):
                    return lambda idx, combo=exe_name_combo: self.on_exe_name_changed(combo.itemData(idx), button_index)

                exe_name_combo.currentIndexChanged.connect(create_handler(index))

                exe_name_combo.setEditable(True)
                exe_name_combo.setEnabled(current_task["task_type"] != "program_window_any")
                if current_task["task_type"] == "program_window_any":
                    exe_name_combo.setCurrentText("")

                dropdowns_layout.addWidget(exe_name_combo)
                content_layout.addLayout(dropdowns_layout)

                # Add all dropdowns and content to the right of the header label
                frame_layout.addLayout(content_layout)

                # Store references to widgets for saving
                task_type_combo.setProperty("button_index", index)
                exe_name_combo.setProperty("button_index", index)

                # Connect signals
                task_type_combo.currentTextChanged.connect(self.on_task_type_changed)

                # Add button frame to column
                column_layout.addWidget(button_frame)

            # Add stretch at the end of each column to push widgets to the top
            column_layout.addStretch()

            # Add the column to the scroll layout
            scroll_layout.addWidget(column_widget)

        # Create button container
        button_container = QHBoxLayout()

        # Add reset button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.setObjectName("buttonConfigButton")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_container.addWidget(reset_button)

        # Add save button
        save_button = QPushButton("Save Changes")
        save_button.setObjectName("buttonConfigButton")
        save_button.clicked.connect(self.save_changes)
        button_container.addWidget(save_button)

        main_layout.addLayout(button_container)

    def create_scroll_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        return scroll, scroll_layout

    def reset_single_frame(self):
        """Reset the dropdowns of a single button frame."""
        sender = self.sender()
        button_index = sender.property("button_index")

        if button_index is None:
            return

        # Find the parent button frame
        button_frame = sender.parent()

        # Find the task type combo box
        task_type_combo = button_frame.findChild(QComboBox)
        if task_type_combo:
            task_type_combo.setCurrentText("program_window_any")

            # Find the corresponding exe name combo box
            exe_name_combo = button_frame.findChild(QComboBox, None)
            if exe_name_combo and exe_name_combo != task_type_combo:
                exe_name_combo.setCurrentText("")
                exe_name_combo.setEnabled(False)

            # Update internal data
            self.button_info.update_button(button_index, {
                "task_type": "program_window_any",
                "properties": {"exe_name": ""}
            })

        self.update_window_title()

    def reset_to_defaults(self):
        """Reset all dropdowns to default values."""
        reply = QMessageBox.question(
            self, "Reset Confirmation",
            "Are you sure you want to reset all settings to default?\nYou can still discard the changes afterwards.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for button_frame in self.findChildren(QFrame, "buttonConfigFrame"):
                # Find the task type combo box
                task_type_combo = button_frame.findChild(QComboBox)
                if task_type_combo:
                    button_index = task_type_combo.property("button_index")
                    task_type_combo.setCurrentText("program_window_any")

                    # Find the exe name combo box in the same frame
                    exe_name_combo = button_frame.findChild(QComboBox, None)
                    if exe_name_combo and exe_name_combo != task_type_combo:
                        exe_name_combo.setCurrentText("")
                        exe_name_combo.setEnabled(False)

                    # Update internal data
                    self.button_info.update_button(button_index, {
                        "task_type": "program_window_any",
                        "properties": {"exe_name": ""}
                    })

            self.update_window_title()

    def closeEvent(self, event):
        """Handle unsaved changes on close."""
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
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def on_task_type_changed(self, new_task_type):
        sender = self.sender()
        button_index = sender.property("button_index")
        try:
            # Find the corresponding exe_name_combo for this button
            button_frame = sender.parent().parent()  # QFrame containing the button's widgets
            exe_name_combo = None
            for child in button_frame.findChildren(QComboBox):
                if child.property("button_index") == button_index and child != sender:
                    exe_name_combo = child
                    break

            if exe_name_combo:
                if new_task_type == "program_window_any":
                    exe_name_combo.setCurrentText("")
                    exe_name_combo.setEnabled(False)
                else:
                    exe_name_combo.setEnabled(True)

            self.button_info.update_button(button_index, {
                "task_type": new_task_type,
                "properties": {"exe_name": "" if new_task_type == "program_window_any" else exe_name_combo.currentText()}
            })
            self.update_window_title()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update task type: {str(e)}")

    def on_exe_name_changed(self, new_exe_name, button_index):
        try:
            self.button_info.update_button(button_index, {
                "properties": {"exe_name": new_exe_name}
            })
            self.update_window_title()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update exe name: {str(e)}")

    def update_window_title(self):
        """Update window title to show unsaved changes"""
        title = "Button Info Editor"
        if self.button_info.has_unsaved_changes:
            title += " *"
        self.setWindowTitle(title)

    def save_changes(self):
        try:
            self.button_info.save_to_json()
            self.button_info.load_json()  # This ensures the object is refreshed with the saved data

            self.update_window_title()
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")


def main():
    import sys
    app = QApplication(sys.argv)
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
    editor = ButtonInfoEditor()
    editor.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
