import subprocess
import json


def list_audio_devices():
    """
    Lists all audio devices (both Playback and Recording) with all their attributes.

    Returns:
        tuple: Two lists containing the playback and recording devices.
    """
    try:
        # PowerShell command to list all devices
        command = [
            "powershell",
            "-Command",
            "Get-AudioDevice -List | ConvertTo-Json"
        ]

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8').strip()

        # Check if the command succeeded
        if result.returncode == 0:
            # Parse the output as JSON
            devices = json.loads(output)

            if isinstance(devices, list):  # Expecting a list of devices
                playback_devices = []
                recording_devices = []

                # Split devices into Playback and Recording
                for device in devices:
                    if device.get('Type') == 'Playback':
                        playback_devices.append(device)
                    elif device.get('Type') == 'Recording':
                        recording_devices.append(device)

                return playback_devices, recording_devices
            else:
                print("Error: The output is not a list of devices.")
                return [], []
        else:
            print("Error: Could not retrieve audio devices.")
            print(result.stderr.decode('utf-8'))
            return [], []

    except Exception as e:
        print(f"An error occurred: {e}")
        return [], []


def set_default_recording_device(device_id):
    """
    Sets the default recording device to the one with the specified device ID.

    Args:
        device_id (str): The Device ID of the recording device to set as default.
    """
    if not device_id:
        print("Error: Invalid Device ID.")
        return

    try:
        # PowerShell command to set the default recording device
        command = [
            "powershell",
            "-Command",
            f"Set-AudioDevice -ID \"{device_id}\""
        ]

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            print(f"Successfully set the default recording device to {device_id}.")
        else:
            print(f"Error: Could not set the default recording device.")
            print(result.stderr.decode('utf-8'))

    except Exception as e:
        print(f"An error occurred: {e}")


def switch_default_recording_device():
    """
    Switches the default recording device to the next device in the list (or the first if none is next).
    """
    # Fetch the devices (filtered into playback and recording)
    playback_devices, recording_devices = list_audio_devices()

    # Ensure that there are recording devices
    if not recording_devices:
        print("No recording devices found.")
        return

    # Find the default recording device
    default_device = next((device for device in recording_devices if device['Default']), None)

    if default_device:
        # Get the index of the current default recording device
        current_index = recording_devices.index(default_device)

        # Find the next device or wrap around to the first one
        next_device = recording_devices[(current_index + 1) % len(recording_devices)]

        # Check if the next device has a valid ID
        device_id = next_device.get("ID", None)
        if device_id:
            print(f"Setting the next recording device (ID: {device_id}) as default.")
            set_default_recording_device(device_id)
        else:
            print("Error: Device ID is missing for the next recording device.")
    else:
        print("No default recording device found.")


# Example usage
switch_default_recording_device()
