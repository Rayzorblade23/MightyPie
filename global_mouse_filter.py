from typing import Any

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtGui import QMouseEvent


class GlobalMouseFilter(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Reference to the main pie_window or specific widgets

    def eventFilter(self, obj, filtered_event):
        # Check for mouse events
        if isinstance(filtered_event, QMouseEvent):
            global_pos = filtered_event.globalPosition().toPoint()

            # Navigate the hierarchy to find the donut_button
            task_switcher_pie: Any | None = getattr(self.main_window, 'pm_task_switcher', None)
            if task_switcher_pie and hasattr(task_switcher_pie, 'donut_button'):
                donut_button = task_switcher_pie.donut_button
                if filtered_event.type() == QEvent.Type.MouseMove:
                    local_pos = donut_button.mapFromGlobal(global_pos)
                    # print(f"Local position on donut_button: {local_pos}")
                    donut_button.turn_towards_cursor(local_pos)

        return super().eventFilter(obj, filtered_event)

