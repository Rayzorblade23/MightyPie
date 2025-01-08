import subprocess
import pyautogui


def open_audio_settings(self, hide_parent=False):
    """Open the Windows 10 audio settings"""
    try:
        subprocess.run(["explorer", "ms-settings:sound"], check=False)
        if hide_parent and self.parent():
            self.parent().hide()  # Hide the parent window after the button is pressed
    except FileNotFoundError:
        print("Error: Explorer or ms-settings:sound command not found.")
    except subprocess.CalledProcessError as e:
        print(f"Error opening audio settings: {e}")


def open_network_settings(self, hide_parent=False):
    """Open the Windows 10 network settings"""
    try:
        subprocess.run(["explorer", "ms-settings:network-status"], check=False)
        if hide_parent and self.parent():
            self.parent().hide()  # Hide the parent window after the button is pressed
    except FileNotFoundError:
        print("Error: Explorer or ms-settings:network-status command not found.")
    except subprocess.CalledProcessError as e:
        print(f"Error opening network settings: {e}")


def open_projection_settings(self, hide_parent=False):
    """Open the Windows 10 projection settings (Win + P)"""
    try:
        pyautogui.hotkey('win', 'p')  # Simulate pressing Win + P
        if hide_parent and self.parent():
            self.parent().hide()  # Hide the parent window after the button is pressed
    except Exception as e:
        print(f"Error opening projection settings: {e}")


def open_onscreen_keyboard(self, hide_parent=False):
    """Open the Windows On-Screen Touch Keyboard"""
    try:
        pyautogui.hotkey('win', 'ctrl', 'o')  # Simulate pressing Win + Ctrl + o
        if hide_parent and self.parent():
            self.parent().hide()  # Hide the parent window after the button is pressed
    except Exception as e:
        print(f"Error opening touch keyboard: {e}")


def open_start_menu(self, hide_parent=False):
    """Simulate pressing Ctrl + Esc to open the Start menu"""
    try:
        pyautogui.FAILSAFE = False  # Disable fail-safe temporarily
        pyautogui.hotkey('ctrl', 'esc')  # Simulate pressing Ctrl + Esc
        if hide_parent and self.parent():
            self.parent().hide()  # Hide the parent window after the button is pressed
    except Exception as e:
        print(f"Error pressing Ctrl + Esc: {e}")
    finally:
        pyautogui.FAILSAFE = True  # Re-enable fail-safe


def open_action_center(self, hide_parent=False):
    """Open the Windows 10 Action Center"""
    try:
        pyautogui.FAILSAFE = False  # Disable fail-safe temporarily
        pyautogui.hotkey('win', 'a')  # Simulate pressing Win + A
        if hide_parent and self.parent():
            self.parent().hide()  # Hide the parent window after the button is pressed
    except Exception as e:
        print(f"Error opening Action Center: {e}")
    finally:
        pyautogui.FAILSAFE = True  # Re-enable fail-safe


def open_explorer_window(self, hide_parent=False):
    """Simulate pressing Windows + E to open an Explorer Window"""
    try:
        pyautogui.hotkey('win', 'e')  # Simulate pressing Win + E
        if hide_parent and self.parent():
            self.parent().hide()  # Hide the parent window after the button is pressed
    except Exception as e:
        print(f"Error pressing Win + e: {e}")

def open_task_manager(self, hide_parent=False):
    """Simulate pressing Ctrl + Shift + Esc to open the Start menu"""
    try:
        pyautogui.FAILSAFE = False  # Disable fail-safe temporarily
        pyautogui.hotkey('ctrl', 'shift', 'esc')  # Simulate pressing Ctrl + Shift + Esc
        if hide_parent and self.parent():
            self.parent().hide()  # Hide the parent window after the button is pressed
    except Exception as e:
        print(f"Error pressing Ctrl + Shift + Esc: {e}")
    finally:
        pyautogui.FAILSAFE = True  # Re-enable fail-safe