from typing import Any

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtGui import QMouseEvent


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
                elif filtered_event.type() == QEvent.Type.MouseButtonRelease:
                    self.handle_mouse_release(global_pos)


        return super().eventFilter(obj, filtered_event)

    def handle_mouse_move(self, global_pos):
        local_pos = self.area_button.mapFromGlobal(global_pos)
        in_area = self.area_button.check_active_area(local_pos.x(), local_pos.y())

        if in_area != self.area_button.in_active_area:
            print("Whaa..")
            self.area_button.in_active_area = in_area
            self.area_button.update_child_button_hover_state(self.task_switcher_pie.pie_buttons[0],in_area)
            self.area_button.set_hover_pos(global_pos)  # Directly pass global position without adjustments

    def handle_mouse_press(self, global_pos):
        local_pos = self.area_button.mapFromGlobal(global_pos)
        if self.area_button.check_active_area(local_pos.x(), local_pos.y()):
            self.area_button.is_pressed = True
            self.task_switcher_pie.pie_buttons[0].setDown(True)
            self.area_button.update()  # Request a repaint to show the dot

            # print("Pressed in active area")

    def handle_mouse_release(self, global_pos):
        if self.area_button.is_pressed:
            self.area_button.is_pressed = False
            self.task_switcher_pie.pie_buttons[0].setDown(False)

            local_pos = self.area_button.mapFromGlobal(global_pos)
            if self.area_button.check_active_area(local_pos.x(), local_pos.y()):
                self.task_switcher_pie.pie_buttons[0].click()
                # print("Released in active area - clicked")
            else:
                print("Released outside active area")
