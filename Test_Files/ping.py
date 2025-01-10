import socket
import threading

def check_ethernet_connection():
    try:
        # Attempt to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=10)
        return True
    except (socket.timeout, OSError):
        return False

def periodic_check(interval=5):
    def check():
        if check_ethernet_connection():
            print("Got internet.")
        else:
            print("Got no internet.")
        # Schedule the next check
        threading.Timer(interval, check).start()

    check()  # Start the first check

# Start periodic checks every 5 seconds
periodic_check(5)

import subprocess
import os


# Function to open a command or execute a keypress
def open_flyout(option):
    commands = {
        # Audio-Related Flyouts
        "volume_mixer": "sndvol",
        "sound_settings": "ms-settings:sound",
        "playback_devices": "control mmsys.cpl",
        "spatial_sound": "ms-settings:spatialsound",
        "audio_accessibility": "ms-settings:easeofaccess-audio",

        # Video/Display-Related Flyouts
        "display_settings": "ms-settings:display",
        "graphics_settings": "ms-settings:display-advancedgraphics",
        "projection": "ms-settings-connectabledevices:projection",
        "night_light": "ms-settings:nightlight",
        "video_playback": "ms-settings:apps-videoplayback",

        # Network-Related Flyouts
        "network_settings": "ms-settings:network",
        "wifi_settings": "ms-settings:network-wifi",
        "ethernet_settings": "ms-settings:network-ethernet",
        "mobile_hotspot": "ms-settings:network-mobilehotspot",
        "data_usage": "ms-settings:datausage",
        "airplane_mode": "ms-settings:network-airplanemode",
        "advanced_network_settings": "ms-settings:network-advancedsettings",

        # General Media-Related
        "bluetooth_settings": "ms-settings:bluetooth",
        "casting": "ms-settings:connectabledevices",
        "media_streaming": "control /name Microsoft.MediaStreaming",

        # Open Action Center (Quick Settings) - Simulate Keypress
        "action_center": "keypress",  # Special case for WIN+A
    }

    if option in commands:
        command = commands[option]
        if command == "keypress":
            import pyautogui  # Install with `pip install pyautogui`
            pyautogui.hotkey("win", "a")
        else:
            try:
                subprocess.run(command, shell=True)
            except Exception as e:
                print(f"Error opening {option}: {e}")
    else:
        print("Invalid option. Please choose a valid flyout.")


# Menu for choosing flyouts
if __name__ == "__main__":
    print("Select a flyout to open:")
    options = [
        "volume_mixer", "sound_settings", "playback_devices", "spatial_sound", "audio_accessibility",
        "display_settings", "graphics_settings", "projection", "night_light", "video_playback",
        "network_settings", "wifi_settings", "ethernet_settings", "mobile_hotspot", "data_usage",
        "airplane_mode", "advanced_network_settings", "bluetooth_settings", "casting", "media_streaming",
        "action_center"
    ]
    for idx, opt in enumerate(options, 1):
        print(f"{idx}. {opt}")

    choice = int(input("Enter the number of your choice: ")) - 1
    if 0 <= choice < len(options):
        open_flyout(options[choice])
    else:
        print("Invalid choice. Exiting.")
