from typing import Any

from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtGui import QMouseEvent


class GlobalMouseFilter(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Reference to the main pie_window or specific widgets
        self.area_button = None
        self.pie_menu: Any | None = getattr(self.main_window, 'pm_task_switcher_1', None)

        self.last_active_child = None  # Track the last active_child value

    def _update_pie_menu(self):
        """Update the task switcher dynamically based on active_child."""
        active_child = getattr(self.main_window, 'active_child', None)

        # Check if the active_child has changed
        if active_child != self.last_active_child:
            pie_menu_map = {
                1: 'pm_task_switcher_1',
                2: 'pm_task_switcher_2',
                3: 'pm_win_control'
            }

            # Get the attribute name based on active_child value
            attribute_name = pie_menu_map.get(active_child)

            # print(f"Mousey thinks it's {attribute_name}.")

            # Only set pie_window.pie_menu if a valid attribute name is found
            if attribute_name and hasattr(self.main_window, attribute_name):
                self.pie_menu = getattr(self.main_window, attribute_name, None)
            else:
                self.pie_menu = None  # Ensure pie_menu is None if no valid attribute found

            # Update the last known active_child value
            self.last_active_child = active_child

    def eventFilter(self, obj, filtered_event):
        # Dynamically update the task switcher on each event
        self._update_pie_menu()

        # Skip processing if the main window or task switcher is hidden or disabled
        if not self.main_window.isVisible() or not self.main_window.isEnabled():
            return super().eventFilter(obj, filtered_event)

        # Check for mouse events
        if isinstance(filtered_event, QMouseEvent):
            global_pos = filtered_event.globalPosition().toPoint()

            # Navigate the hierarchy to find the donut_button
            if self.pie_menu and hasattr(self.pie_menu, 'donut_button'):
                donut_button = self.pie_menu.donut_button
                if filtered_event.type() == QEvent.Type.MouseMove:
                    local_pos = donut_button.mapFromGlobal(global_pos)
                    # print(f"Local position on donut_button: {local_pos}")
                    donut_button.turn_towards_cursor(local_pos)

            if self.pie_menu and hasattr(self.pie_menu, 'area_button'):
                self.area_button = self.pie_menu.area_button
                if filtered_event.type() == QEvent.Type.MouseMove:
                    self.handle_mouse_move(global_pos)
                elif filtered_event.type() == QEvent.Type.MouseButtonPress:
                    self.handle_mouse_press(filtered_event)  # Pass the QMouseEvent instead
                elif filtered_event.type() == QEvent.Type.MouseButtonRelease:
                    self.handle_mouse_release(filtered_event)  # Pass the event directly

        return super().eventFilter(obj, filtered_event)

    def handle_mouse_move(self, global_pos):
        local_pos = self.area_button.mapFromGlobal(global_pos)
        # active_section will be -1 if not in any area, 0-7 if in a valid section
        active_section = self.area_button.check_active_area(local_pos.x(), local_pos.y())

        if active_section != getattr(self.area_button, 'current_active_section', -1):
            # Reset previous button's hover state if there was one
            prev_section = getattr(self.area_button, 'current_active_section', -1)
            if prev_section != -1:
                self.pie_menu.update_child_button_hover_state(
                    self.pie_menu.pie_buttons[prev_section], False)

            # Update for new section
            self.area_button.current_active_section = active_section
            if active_section != -1:
                self.pie_menu.update_child_button_hover_state(
                    self.pie_menu.pie_buttons[active_section], True)

            self.area_button.set_hover_pos(global_pos)

    def handle_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            local_pos = self.area_button.mapFromGlobal(global_pos)
            active_section = self.area_button.check_active_area(local_pos.x(), local_pos.y())

            if active_section != -1:
                self.area_button.is_pressed = True
                self.area_button.pressed_section = active_section  # Store which section was pressed
                self.pie_menu.pie_buttons[active_section].setDown(True)
                self.area_button.update()
        elif event.button() == Qt.MouseButton.RightButton:
            global_pos = event.globalPosition().toPoint()
            local_pos = self.area_button.mapFromGlobal(global_pos)
            active_section = self.area_button.check_active_area(local_pos.x(), local_pos.y())

            if active_section != -1:
                self.area_button.is_pressed = True
                self.area_button.pressed_section = active_section  # Store which section was pressed
                self.pie_menu.pie_buttons[active_section].setDown(True)
                self.area_button.update()
        elif event.button() == Qt.MouseButton.MiddleButton:
            global_pos = event.globalPosition().toPoint()
            local_pos = self.area_button.mapFromGlobal(global_pos)
            active_section = self.area_button.check_active_area(local_pos.x(), local_pos.y())

            if active_section != -1:
                self.area_button.is_pressed = True
                self.area_button.pressed_section = active_section  # Store which section was pressed
                self.pie_menu.pie_buttons[active_section].setDown(True)
                self.area_button.update()

    def handle_mouse_release(self, event: QMouseEvent):
        global_pos = event.globalPosition().toPoint()
        local_pos = self.area_button.mapFromGlobal(global_pos)
        released_section = self.area_button.check_active_area(local_pos.x(), local_pos.y())

        if self.area_button.is_pressed:
            self.area_button.is_pressed = False
            pressed_section = getattr(self.area_button, 'pressed_section', -1)

            if pressed_section != -1:
                self.pie_menu.pie_buttons[pressed_section].setDown(False)

                # Check if released in the same section
                if released_section == pressed_section:
                    if event.button() == Qt.MouseButton.LeftButton:
                        self.pie_menu.pie_buttons[released_section].trigger_left_click_action()
                    elif event.button() == Qt.MouseButton.RightButton:
                        self.pie_menu.pie_buttons[released_section].trigger_right_click_action()
                    elif event.button() == Qt.MouseButton.MiddleButton:
                        self.pie_menu.pie_buttons[released_section].trigger_middle_click_action()
                else:
                    print(f"Released in a different section or outside (pressed: {pressed_section}, released: {released_section})")

            self.area_button.pressed_section = -1  # Reset pressed section
