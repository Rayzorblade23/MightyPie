from typing import Tuple, TYPE_CHECKING, cast

from PyQt6.QtGui import QRegion
from pynput.mouse import Controller, Button

from src.data.config import CONFIG
from src.gui.buttons.expanded_button import ExpandedButton
from src.utils.program_utils import main_window_hide

if TYPE_CHECKING:
    from src.gui.pie_window import PieWindow
    from src.gui.menus.pie_menu import PieMenu


class PieMenuMiddleButton(ExpandedButton):
    """Class for creating a custom button with overridden behavior."""

    button_map = {
        'forward': lambda controller: [controller.press(Button.x2), controller.release(Button.x2)],
        'backward': lambda controller: [controller.press(Button.x1), controller.release(Button.x1)],
        'nothing': lambda controller: None,  # No action for 'nothing'
    }

    def __init__(self, text: str, object_name: str, pos: Tuple[int, int], parent=None):
        """Initialize the custom button with additional properties."""
        super().__init__(text, object_name, parent=parent)

        self.pie_menu_parent: "PieMenu" = parent
        self.main_window: "PieWindow" = cast("PieWindow", self.pie_menu_parent.parent)
        self.radius = CONFIG.INTERNAL_INNER_RADIUS

        self.button_action = CONFIG.CENTER_BUTTON

        self.set_size(fixed_size=True, size=(self.radius * 2, self.radius * 2))

        self.set_pos(pos=pos)

        self.left_clicked.connect(
            lambda: [
                main_window_hide(),
                self.handle_left_click_action()
            ]
        )

        self.right_clicked.connect(lambda: main_window_hide())
        self.middle_clicked.connect(lambda: self.main_window.open_special_menu())

        self.lower()

    def handle_left_click_action(self):
        """Handle button press/release based on the action (forward, backward, nothing)."""
        controller = Controller()  # Create an instance of Controller once

        # Call the appropriate action based on the button_action value
        action = self.button_map.get(self.button_action)
        if action:
            action(controller)  # Execute the action

    def resizeEvent(self, event):
        """Reapply circular mask whenever the size changes."""
        super().resizeEvent(event)
        self.apply_circle_mask()

    def apply_circle_mask(self):
        """Apply a circular mask to the button."""
        mask = QRegion(0, 0, self.width(), self.height(), QRegion.RegionType.Ellipse)
        self.setMask(mask)