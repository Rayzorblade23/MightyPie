from typing import Any

from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.sip import isdeleted


class GlobalMouseFilter(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Reference to the main main_window or specific widgets
        self.area_button = None
        self.pie_menu: Any | None = None  # Initially, no PieMenu is selected
        self.last_active_child = None  # Track the last active_child value

    def _update_pie_menu(self):
        """Update the task switcher dynamically based on active_child."""
        active_child = getattr(self.main_window, 'active_child', None)

        # Check if the active_child has changed
        if active_child != self.last_active_child:
            self.pie_menu = self._get_pie_menu_for_active_child(active_child)
            self.last_active_child = active_child

    def _get_pie_menu_for_active_child(self, active_child):
        """Map the active_child to the appropriate pie menu."""
        end_task_switchers = len(self.main_window.pie_menus_primary)
        end_win_controls = len(self.main_window.pie_menus_primary) + len(self.main_window.pie_menus_secondary)

        if isinstance(active_child, int):
            if 1 <= active_child <= end_task_switchers:
                return self.main_window.pie_menus_primary[active_child - 1]
            elif end_task_switchers < active_child <= end_win_controls:
                return self.main_window.pie_menus_secondary[active_child - 1 - end_task_switchers]

        return None

    def eventFilter(self, obj, filtered_event):
        """Filter mouse events and handle accordingly."""
        if isdeleted(self.main_window):
            return False

        self._update_pie_menu()

        # Skip processing if the main window or task switcher is hidden or disabled
        if not self.main_window.isVisible() or not self.main_window.isEnabled():
            return super().eventFilter(obj, filtered_event)

        if isinstance(filtered_event, QMouseEvent):
            global_pos = filtered_event.globalPosition().toPoint()

            if self.pie_menu and hasattr(self.pie_menu, 'indicator'):
                self._handle_indicator_mouse_move(filtered_event, global_pos)

            if self.pie_menu and hasattr(self.pie_menu, 'area_button'):
                self.area_button = self.pie_menu.area_button
                self._handle_mouse_event(filtered_event, global_pos)

        return super().eventFilter(obj, filtered_event)

    def _handle_indicator_mouse_move(self, event: QMouseEvent, global_pos):
        """Handle mouse move events for the pie menu indicator."""
        if event.type() == QEvent.Type.MouseMove:
            indicator = self.pie_menu.indicator
            local_pos = indicator.mapFromGlobal(global_pos)
            indicator.turn_towards_cursor(local_pos)

    def _handle_mouse_event(self, event: QMouseEvent, global_pos):
        """Handle mouse move, press, and release events."""
        if event.type() == QEvent.Type.MouseMove:
            self.handle_mouse_move(global_pos)
        elif event.type() == QEvent.Type.MouseButtonPress:
            self.handle_mouse_press(event)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.handle_mouse_release(event)

    def handle_mouse_move(self, global_pos):
        """Handle mouse move event on the pie menu's area button."""
        local_pos = self.area_button.mapFromGlobal(global_pos)
        active_section = self._get_active_section(local_pos)

        if active_section != getattr(self.area_button, 'current_active_section', -1):
            self._update_hover_state(active_section)
            self.area_button.set_hover_pos(global_pos)

    def _get_active_section(self, local_pos):
        """Determine the active section based on local position."""
        return self.area_button.check_active_area(local_pos.x(), local_pos.y())

    def _update_hover_state(self, active_section):
        """Update the hover state of the pie button."""
        prev_section = getattr(self.area_button, 'current_active_section', -1)

        if prev_section != -1:
            self.pie_menu.pie_buttons[prev_section].update_hover_state(False)

        self.area_button.current_active_section = active_section
        if active_section != -1:
            self.pie_menu.pie_buttons[active_section].update_hover_state(True)

    def handle_mouse_press(self, event: QMouseEvent):
        """Handle mouse press events for all mouse buttons."""
        global_pos = event.globalPosition().toPoint()
        local_pos = self.area_button.mapFromGlobal(global_pos)
        active_section = self._get_active_section(local_pos)

        if active_section != -1:
            self._set_pressed_state(active_section)
            self._trigger_button_press(active_section)

    def _set_pressed_state(self, active_section):
        """Set the pressed state for the area button."""
        self.area_button.is_pressed = True
        self.area_button.pressed_section = active_section

    def _trigger_button_press(self, active_section):
        """Trigger the corresponding action for the button press."""
        self.pie_menu.pie_buttons[active_section].setDown(True)
        self.area_button.update()

    def handle_mouse_release(self, event: QMouseEvent):
        """Handle mouse release events for all mouse buttons."""
        global_pos = event.globalPosition().toPoint()
        local_pos = self.area_button.mapFromGlobal(global_pos)
        released_section = self._get_active_section(local_pos)

        if self.area_button.is_pressed:
            self._reset_pressed_state(released_section, event)

    def _reset_pressed_state(self, released_section, event: QMouseEvent):
        """Reset the pressed state and trigger the appropriate action."""
        self.area_button.is_pressed = False
        pressed_section = getattr(self.area_button, 'pressed_section', -1)

        if pressed_section != -1:
            self.pie_menu.pie_buttons[pressed_section].setDown(False)

            if released_section == pressed_section:
                self._trigger_button_release(pressed_section, event)

            self.area_button.pressed_section = -1  # Reset pressed section

    def _trigger_button_release(self, pressed_section, event: QMouseEvent):
        """Trigger the appropriate action for the button release."""
        button = self.pie_menu.pie_buttons[pressed_section]

        if event.button() == Qt.MouseButton.LeftButton:
            button.trigger_left_click_action()
        elif event.button() == Qt.MouseButton.RightButton:
            button.trigger_right_click_action()
        elif event.button() == Qt.MouseButton.MiddleButton:
            button.trigger_middle_click_action()
