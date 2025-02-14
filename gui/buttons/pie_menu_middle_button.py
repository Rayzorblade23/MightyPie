from typing import Tuple, TYPE_CHECKING, cast

from pynput.mouse import Controller, Button

from data.config import CONFIG
from gui.buttons.expanded_button import ExpandedButton
from utils.program_utils import main_window_hide

if TYPE_CHECKING:
    from gui.pie_window import PieWindow
    from gui.menus.pie_menu import PieMenu


class PieMenuMiddleButton(ExpandedButton):
    """Class for creating a custom button with overridden behavior."""

    def __init__(self, text: str, object_name: str, pos: Tuple[int, int], parent=None):
        """Initialize the custom button with additional properties."""
        super().__init__(text, object_name, parent=parent)

        self.pie_menu_parent: "PieMenu" = parent
        self.main_window: "PieWindow" = cast("PieWindow", self.pie_menu_parent.parent())
        self.radius = CONFIG.INTERNAL_INNER_RADIUS

        self.set_size(fixed_size=True, size=(self.radius * 2, self.radius * 2))

        self.set_pos(pos=pos)

        self.left_clicked.connect(
            lambda: [main_window_hide(), Controller().press(Button.x2), Controller().release(Button.x2)])
        self.right_clicked.connect(lambda: main_window_hide())
        self.middle_clicked.connect(lambda: self.main_window.open_special_menu())

        self.lower()
