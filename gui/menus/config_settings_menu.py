from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QCheckBox, QSpinBox, QWidget,
                             QPushButton, QScrollArea, QMessageBox, QSizePolicy, QColorDialog)

from data.config import CONFIG, DefaultConfig
from utils.file_handling_utils import get_resource_path
from utils.icon_utils import get_icon
from utils.program_utils import restart_program


class NoScrollSpinBox(QSpinBox):
    """QComboBox that ignores mouse wheel scrolling."""

    def wheelEvent(self, event):
        event.ignore()  # Prevents the wheel from changing the selection

class ConfigSettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{CONFIG.INTERNAL_PROGRAM_NAME} Settings")
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

        # Save and Restart button
        save_and_restart_button = QPushButton("Save && Restart")
        save_and_restart_button.clicked.connect(self.save_settings_and_restart)

        # Reset button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)

        # Assemble button layout
        button_layout.addWidget(save_button)
        button_layout.addWidget(save_and_restart_button)
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
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row_layout.addWidget(label)

        # Input based on type
        if setting['type'] == "<class 'bool'>":
            input_widget = QCheckBox()
            input_widget.setChecked(setting['value'])
            row_layout.addWidget(input_widget)
        elif setting['type'] in ["<class 'int'>", "<class 'float'>"]:
            input_widget = NoScrollSpinBox()
            input_widget.setRange(1, 9999)  # Set appropriate min/max range
            input_widget.setValue(setting['value'])
            row_layout.addWidget(input_widget)
        elif setting['type'] == "<class 'str'>":  # Handle string type (color hex code)
            input_widget = QLineEdit(str(setting['value']))

            # Create a color picker button if it's a hex color
            if input_widget.text().startswith("#"):
                # Create a color picker button
                color_picker_button = QPushButton()
                color_picker_button.setToolTip("Pick Color")
                color_picker_button.setIcon(get_icon("palette", is_inverted=True))
                color_picker_button.setFixedSize(24, 20)
                color_picker_button.setObjectName("buttonConfigSingleResetButton")

                color_picker_button.clicked.connect(lambda: self.pick_color(input_widget, color_picker_button))

                # Update the color preview
                color_picker_button.setStyleSheet(f"background-color: {input_widget.text()};")

                # Connect the QLineEdit to update the color picker button
                input_widget.textChanged.connect(lambda: self.update_color_preview(input_widget, color_picker_button))

                # Create a layout specifically for the color field and the picker button
                color_field_and_picker_layout = QHBoxLayout()
                color_field_and_picker_layout.addWidget(input_widget)
                color_field_and_picker_layout.addWidget(color_picker_button)

                # Add the color picker layout to the main row layout
                row_layout.addLayout(color_field_and_picker_layout)
            else:
                row_layout.addWidget(input_widget)
        else:
            input_widget = QLineEdit(str(setting['value']))
            row_layout.addWidget(input_widget)

        input_widget.setObjectName(setting['name'])
        self.setting_widgets[setting['name']] = input_widget

        # Reset button for this specific setting
        reset_button = QPushButton()
        reset_button.setToolTip("Reset")
        reset_button.setIcon(get_icon("restart", is_inverted=True))
        reset_button.setFixedSize(24, 20)
        reset_button.setObjectName("buttonConfigSingleResetButton")
        reset_button.clicked.connect(
            lambda _, widget=input_widget, setting_name=setting['name']: self.reset_single_setting(widget, setting_name))
        row_layout.addWidget(reset_button)

        # Ensure that all widgets in this row are stretched evenly
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        input_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        reset_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        return row_layout

    @staticmethod
    def update_color_preview(input_widget, color_picker_button):
        """Updates the color preview button when the QLineEdit text changes."""
        color_text = input_widget.text()
        if color_text.startswith("#"):  # Only update if the text is a valid hex code
            color_picker_button.setStyleSheet(f"background-color: {color_text};")

    def pick_color(self, input_widget, color_picker_button):
        """Opens a color picker and sets the selected color as a hex code in the QLineEdit."""
        initial_color = QColor(input_widget.text()) if input_widget.text().startswith("#") else QColor()
        color = QColorDialog.getColor(initial_color, self, "Pick a Color")

        if color.isValid():
            # Set the color as a hex string (e.g., #RRGGBB)
            hex_color = color.name()
            input_widget.setText(hex_color)

            # Update the color picker button's background color to match the selected color
            color_picker_button.setStyleSheet(f"background-color: {hex_color};")


    def save_settings(self):
        for name, widget in self.setting_widgets.items():
            value = self._get_widget_value(widget)
            CONFIG.update_setting(name, value)
        self.close()

    def save_settings_and_restart(self):
        for name, widget in self.setting_widgets.items():
            value = self._get_widget_value(widget)
            CONFIG.update_setting(name, value)
        restart_program()

    def reset_to_defaults(self):
        # Create a confirmation dialog
        reply = QMessageBox.question(
            self, 'Reset Confirmation',
            'Are you sure you want to reset all settings to default values?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Get default values from the original TaskPieSwitcherConfig
            default_config = DefaultConfig()

            # Update widgets with default values
            for name, widget in self.setting_widgets.items():
                default_value = getattr(default_config, name)

                if isinstance(widget, QCheckBox):
                    widget.setChecked(default_value)
                elif isinstance(widget, NoScrollSpinBox):
                    widget.setValue(default_value)
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(default_value))

                # Update the actual configuration
                CONFIG.update_setting(name, default_value)

            CONFIG.save_config()  # Save the config after resetting

            QMessageBox.information(self, 'Reset Complete', 'Settings have been reset to default values.')

    @staticmethod
    def reset_single_setting(widget, setting_name):
        """Resets the given setting to its default value."""
        default_config = DefaultConfig()
        default_value = getattr(default_config, setting_name)

        if isinstance(widget, QCheckBox):
            widget.setChecked(default_value)
        elif isinstance(widget, NoScrollSpinBox):
            widget.setValue(default_value)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(default_value))

        # Update the actual configuration
        CONFIG.update_setting(setting_name, default_value)
        CONFIG.save_config()  # Optionally save after resetting

    @staticmethod
    def _get_widget_value(widget):
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, NoScrollSpinBox):
            return widget.value()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        return None


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    # Load the QSS template
    with open(get_resource_path("../../style.qss"), "r") as file:
        qss_template = file.read()

    # inserting style attributes from the config.py file
    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", CONFIG.ACCENT_COLOR_MUTED)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    # Apply the QSS to the application or widgets
    app.setStyleSheet(qss)
    window = ConfigSettingsWindow()
    window.show()
    app.exec()
