from PyQt6.QtCore import pyqtSignal, pyqtSlot, QTimer, QObject

from data.config import CONFIG
from functions.window_functions import load_cache, launch_app, focus_window_by_handle, close_window_by_handle
from gui.menus.pie_menu import PieMenuType

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui.pie_window import PieWindow

class PieButtonUpdater(QObject):  # Inherit from QObject
    """Class responsible for handling pie button UI updates via signal."""

    update_buttons_signal = pyqtSignal(QObject, list)  # Expect QWidget and list

    def __init__(self):
        """Initialize the PieButtonUpdater instance and connect the signal."""
        super().__init__()  # Call QObject's constructor!
        # Connect the signal to the slot
        self.update_buttons_signal.connect(self.update_button_ui)


    @pyqtSlot(QObject, list)
    def update_button_ui(self, pie_window : "PieWindow", button_updates):
        """Update button UI in the main thread."""
        app_info_cache = load_cache()

        # TODO: Give all the Pie Menus the update, which give the buttons their updates
        #       This can then probably go into PieMenu instead

        for update in button_updates:
            button_index = update["index"]
            button_text_1 = update["properties"]["text_1"]
            button_text_2 = update["properties"]["text_2"]
            window_handle = update["properties"]["window_handle"]
            app_icon_path = update["properties"]["app_icon_path"]
            exe_name = update["properties"]["exe_name"]

            # Determine task switcher and index
            task_switcher, index = pie_window.get_pie_menu_and_index(button_index, PieMenuType.TASK_SWITCHER)

            # Update button text and icon
            pie_window.pie_button_texts[index] = button_text_1
            task_switcher.pie_buttons[index].update_content(button_text_1, button_text_2, app_icon_path)


            # Disconnect any previous connections
            try:
                task_switcher.pie_buttons[index].clicked.disconnect()
            except TypeError:
                pass  # No connections to disconnect

            # Handle reserved button actions
            if window_handle == 0:
                exe_path = app_info_cache.get(exe_name, {}).get("exe_path")
                if exe_path:
                    task_switcher.pie_buttons[index].set_left_click_action(
                        lambda captured_exe_path=exe_path: (
                            pie_window.hide(),
                            QTimer.singleShot(0, lambda: launch_app(captured_exe_path)),
                        )
                    )
                continue

            # Handle window actions
            task_switcher.pie_buttons[index].set_left_click_action(
                lambda hwnd=window_handle: (
                    pie_window.hide(),
                    QTimer.singleShot(0, lambda: focus_window_by_handle(hwnd)),
                )
            )
            task_switcher.pie_buttons[index].set_middle_click_action(
                lambda hwnd=window_handle: (
                    QTimer.singleShot(0, lambda: close_window_by_handle(hwnd)),
                    QTimer.singleShot(100, lambda: pie_window.auto_refresh()),
                )
            )
            task_switcher.pie_buttons[index].setEnabled(True)

        # Clear attributes when button index not among updates
        for i in range(CONFIG._MAX_BUTTONS * CONFIG._NUM_PIE_TASK_SWITCHERS):
            if i not in [update["index"] for update in button_updates]:
                task_switcher, index = pie_window.get_pie_menu_and_index(i, PieMenuType.TASK_SWITCHER)

                # Disable the button
                pie_window.pie_button_texts[index] = "Empty"
                task_switcher.pie_buttons[index].clear()

