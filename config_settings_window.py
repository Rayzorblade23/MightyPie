from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QCheckBox, QSpinBox, QWidget,
                             QPushButton, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt
from config import CONFIG, TaskPieSwitcherConfig


class ConfigSettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{CONFIG.PROGRAM_NAME} Settings")
        self.setMinimumWidth(400)

        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Scroll area for settings
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        settings_layout = QVBoxLayout()

        # Dynamic settings generation
        self.setting_widgets = {}
        for setting in CONFIG.get_settings_for_ui():
            setting_row = self._create_setting_input(setting)
            settings_layout.addLayout(setting_row)

        scroll_content.setLayout(settings_layout)
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)

        # Button layout
        button_layout = QHBoxLayout()

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)

        # Reset button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)

        # Assemble button layout
        button_layout.addWidget(save_button)
        button_layout.addWidget(reset_button)

        # Assemble main layout
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(button_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _create_setting_input(self, setting):
        row_layout = QHBoxLayout()

        # Label
        label = QLabel(setting['name'])
        row_layout.addWidget(label)

        # Input based on type
        if setting['type'] == "<class 'bool'>":
            input_widget = QCheckBox()
            input_widget.setChecked(setting['value'])
        elif setting['type'] in ["<class 'int'>", "<class 'float'>"]:
            input_widget = QSpinBox()
            input_widget.setRange(1, 9999)  # Set appropriate min/max range
            input_widget.setValue(setting['value'])
        else:
            input_widget = QLineEdit(str(setting['value']))

        input_widget.setObjectName(setting['name'])
        self.setting_widgets[setting['name']] = input_widget
        row_layout.addWidget(input_widget)

        return row_layout

    def save_settings(self):
        for name, widget in self.setting_widgets.items():
            value = self._get_widget_value(widget)
            CONFIG.update_setting(name, value)
        self.close()

    def reset_to_defaults(self):
        # Create a confirmation dialog
        reply = QMessageBox.question(
            self, 'Reset Confirmation',
            'Are you sure you want to reset all settings to default values?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Get default values from the original TaskPieSwitcherConfig
            default_config = TaskPieSwitcherConfig()

            # Update widgets with default values
            for name, widget in self.setting_widgets.items():
                default_value = getattr(default_config, name)

                if isinstance(widget, QCheckBox):
                    widget.setChecked(default_value)
                elif isinstance(widget, QSpinBox):
                    widget.setValue(default_value)
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(default_value))

                # Update the actual configuration
                CONFIG.update_setting(name, default_value)

            QMessageBox.information(self, 'Reset Complete', 'Settings have been reset to default values.')

    def _get_widget_value(self, widget):
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        return None


def open_config_window():
    app = QApplication.instance() or QApplication([])
    window = ConfigSettingsWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    open_config_window()