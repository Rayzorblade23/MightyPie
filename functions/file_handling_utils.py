import sys
import os

def get_resource_path(relative_path):
    """
    Get the absolute path to a resource, accounting for PyInstaller bundles.

    Args:
        relative_path: The path to the resource, relative to the script's location.
                       Can use forward slashes ('/') or backward slashes ('\').

    Returns:
        The absolute path to the resource.
    """
    # Normalize the path to use the OS's path separator. This handles both / and \.
    normalized_path = os.path.normpath(relative_path)

    if hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        return os.path.join(sys._MEIPASS, normalized_path)
    # Running in normal Python environment
    return os.path.join(os.path.abspath("."), normalized_path)
