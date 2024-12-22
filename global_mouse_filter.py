from typing import Any

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget, QPushButton


class GlobalMouseFilter(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Reference to the main pie_window or specific widgets
        self.area_button = None
        self.task_switcher_pie: Any | None = getattr(self.main_window, 'pm_task_switcher', None)

    def eventFilter(self, obj, filtered_event):
        # Check for mouse events
        if isinstance(filtered_event, QMouseEvent):
            global_pos = filtered_event.globalPosition().toPoint()

            # Navigate the hierarchy to find the donut_button
            if self.task_switcher_pie and hasattr(self.task_switcher_pie, 'donut_button'):
                donut_button = self.task_switcher_pie.donut_button
                if filtered_event.type() == QEvent.Type.MouseMove:
                    local_pos = donut_button.mapFromGlobal(global_pos)
                    # print(f"Local position on donut_button: {local_pos}")
                    donut_button.turn_towards_cursor(local_pos)

            if self.task_switcher_pie and hasattr(self.task_switcher_pie, 'area_button'):
                self.area_button = self.task_switcher_pie.area_button
                if filtered_event.type() == QEvent.Type.MouseMove:
                    self.handle_mouse_move(global_pos)
                elif filtered_event.type() == QEvent.Type.MouseButtonPress:
                    self.handle_mouse_press(global_pos)
                    # Let other buttons through
                    if isinstance(obj, QPushButton):
                        obj.click()
                elif filtered_event.type() == QEvent.Type.MouseButtonRelease:
                    self.handle_mouse_release(global_pos)


        return super().eventFilter(obj, filtered_event)

    def handle_mouse_move(self, global_pos):
        local_pos = self.area_button.mapFromGlobal(global_pos)
        # active_section will be -1 if not in any area, 0-7 if in a valid section
        active_section = self.area_button.check_active_area(local_pos.x(), local_pos.y())


        if active_section != getattr(self.area_button, 'current_active_section', -1):
            # Reset previous button's hover state if there was one
            prev_section = getattr(self.area_button, 'current_active_section', -1)
            if prev_section != -1:
                self.task_switcher_pie.update_child_button_hover_state(
                    self.task_switcher_pie.pie_buttons[prev_section], False)

            # Update for new section
            self.area_button.current_active_section = active_section
            if active_section != -1:
                self.task_switcher_pie.update_child_button_hover_state(
                    self.task_switcher_pie.pie_buttons[active_section], True)

            self.area_button.set_hover_pos(global_pos)

    def handle_mouse_press(self, global_pos):
        local_pos = self.area_button.mapFromGlobal(global_pos)
        active_section = self.area_button.check_active_area(local_pos.x(), local_pos.y())

        if active_section != -1:
            self.area_button.is_pressed = True
            self.area_button.pressed_section = active_section  # Store which section was pressed
            self.task_switcher_pie.pie_buttons[active_section].setDown(True)
            self.area_button.update()

    def handle_mouse_release(self, global_pos):
        if self.area_button.is_pressed:
            self.area_button.is_pressed = False
            pressed_section = getattr(self.area_button, 'pressed_section', -1)

            if pressed_section != -1:
                self.task_switcher_pie.pie_buttons[pressed_section].setDown(False)

                local_pos = self.area_button.mapFromGlobal(global_pos)
                released_section = self.area_button.check_active_area(local_pos.x(), local_pos.y())

                # Only trigger click if released in same section as pressed
                if released_section == pressed_section:
                    self.task_switcher_pie.pie_buttons[released_section].click()
                else:
                    print(f"Released in different section or outside (pressed: {pressed_section}, released: {released_section})")

            self.area_button.pressed_section = -1  # Reset pressed section
