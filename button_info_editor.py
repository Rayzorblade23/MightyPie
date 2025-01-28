# button_info_editor.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QScrollArea, \
    QPushButton, QFrame, QGridLayout

from button_info import ButtonInfo
from config import CONFIG
from functions.file_handling_functions import get_resource_path


class ButtonInfoEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.button_info = ButtonInfo()

        # Available options for dropdowns
        self.task_types = ["program_window_fixed", "program_window_any"]

        # Get unique app names and exe names from existing configuration
        self.exe_names = set()
        for task in self.button_info.values():
            self.exe_names.add(task["properties"]["exe_name"])

        # Convert to sorted lists and ensure empty option is available
        self.exe_names = sorted(list(self.exe_names)) + [""]

        self.init_ui()

    from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QScrollArea, QWidget,
                                 QLabel, QComboBox, QPushButton, QFrame)
    from PyQt6.QtCore import Qt

    from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QScrollArea, QWidget,
                                 QLabel, QComboBox, QPushButton, QFrame)
    from PyQt6.QtCore import Qt

    def init_ui(self):
        self.setWindowTitle('Button Info Editor')
        self.setGeometry(100, 100, 800, 600)

        # Create the main layout
        main_layout = QVBoxLayout(self)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Calculate number of columns needed
        num_columns = CONFIG.NUM_PIE_TASK_SWITCHERS
        buttons_per_column = CONFIG.MAX_BUTTONS

        # Create columns
        for col in range(num_columns):
            # Create a column container
            column_widget = QWidget()
            column_layout = QVBoxLayout(column_widget)

            # Add column title
            title_label = QLabel(f"Pie Menu {col + 1}")
            title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
            title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            column_layout.addWidget(title_label)

            # Add horizontal line under the title with explicit styling
            title_separator = QFrame()
            title_separator.setFrameStyle(QFrame.Shape.HLine.value)
            title_separator.setLineWidth(1)
            column_layout.addWidget(title_separator)

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
                button_frame.setFrameStyle(QFrame.Shape.Panel.value | QFrame.Shadow.Raised.value)
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

                # Exe name selector
                exe_name_layout = QHBoxLayout()
                exe_name_layout.addWidget(QLabel("Exe Name:"))
                exe_name_combo = QComboBox()
                exe_name_combo.addItems(self.exe_names)
                exe_name_combo.setCurrentText(current_task["properties"]["exe_name"])
                exe_name_combo.setEditable(True)
                exe_name_layout.addWidget(exe_name_combo)
                button_layout.addLayout(exe_name_layout)

                # Store references to widgets for saving
                task_type_combo.setProperty("button_index", index)
                exe_name_combo.setProperty("button_index", index)

                # Connect signals
                task_type_combo.currentTextChanged.connect(self.on_task_type_changed)
                exe_name_combo.currentTextChanged.connect(
                    lambda text, idx=index: self.on_exe_name_changed(text, idx)
                )

                # Add button frame to column
                column_layout.addWidget(button_frame)

            # Add stretch at the end of each column to push widgets to the top
            column_layout.addStretch()

            # Add the column to the scroll layout
            scroll_layout.addWidget(column_widget)

        # Add save button
        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self.save_changes)
        main_layout.addWidget(save_button)

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
            self.button_info.update_button(button_index, {
                "task_type": new_task_type
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
