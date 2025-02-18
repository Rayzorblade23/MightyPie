# gui/menus/button_info_components.py
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton

from utils.button_info_editor_utils import (
    create_texts_layout, create_dropdowns_layout, get_direction
)
from utils.icon_utils import get_icon

if TYPE_CHECKING:
    from gui.menus.button_info_editor import ButtonInfoEditor


class ButtonFrame(QFrame):
    def __init__(self, index: int, row: int, editor: 'ButtonInfoEditor'):
        """
        Initialize a ButtonFrame.

        Args:
            index: The button index
            row: The row number
            editor: The parent ButtonInfoEditor instance
        """
        super().__init__()
        self.index = index
        self.row = row
        self.editor = editor
        self.init_ui()

    def init_ui(self):
        self.setObjectName("buttonConfigFrame")
        self.setFrameStyle(QFrame.Shape.Panel.value | QFrame.Shadow.Raised.value)

        frame_layout = QHBoxLayout(self)
        left_layout = self._create_left_section()
        content_layout = self._create_content_section()

        frame_layout.addLayout(left_layout)
        frame_layout.addLayout(content_layout)

    def _create_left_section(self):
        layout = QVBoxLayout()

        # Header with direction
        header_layout = QHBoxLayout()
        direction = get_direction(self.row)
        header_label = QLabel(f" {direction} ")
        header_label.setObjectName("buttonConfigFrameHeader")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setFixedSize(40, 40)
        header_layout.addStretch()
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Reset button
        reset_button = self._create_reset_button()
        reset_layout = QVBoxLayout()
        reset_layout.addStretch()
        reset_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignCenter)
        reset_layout.addStretch()

        layout.addLayout(header_layout)
        layout.addLayout(reset_layout)
        return layout

    def _create_reset_button(self):
        reset_button = QPushButton()
        reset_button.setToolTip("Reset")
        reset_button.setIcon(get_icon("restart", is_inverted=True))
        reset_button.setFixedSize(24, 20)
        reset_button.setObjectName("buttonConfigSingleResetButton")
        reset_button.setProperty("button_index", self.index)
        reset_button.clicked.connect(self._on_reset_clicked)
        return reset_button

    def _create_content_section(self):
        content_layout = QHBoxLayout()
        current_button_info = self.editor.button_info[self.index]

        task_type_dropdown, exe_name_dropdown = self.editor.create_dropdowns(
            current_button_info, self.index
        )

        content_layout.addLayout(create_texts_layout())
        content_layout.addLayout(create_dropdowns_layout(task_type_dropdown, exe_name_dropdown))
        return content_layout

    def _on_reset_clicked(self):
        from utils.button_info_editor_utils import reset_single_frame
        reset_single_frame(
            sender=self.sender(),
            button_info=self.editor.button_info,
            temp_config=self.editor.temp_config,
            update_window_title=lambda: self.editor.update_window_title()
        )
