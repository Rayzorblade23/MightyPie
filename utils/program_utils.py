import os
import subprocess
import sys
import time

import psutil
from PyQt6.QtCore import QCoreApplication


def restart_program():
    current_pid = os.getpid()
    print(f"Restarting. Current PID: {current_pid}")

    if hasattr(sys, '_instance'):
        sys._instance.release_for_restart()

    for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid and proc.info['cmdline']:
                if sys.argv[0] in proc.info['cmdline']:
                    print(f"Killing old instance: PID {proc.info['pid']}")
                    proc.terminate()
        except psutil.NoSuchProcess:
            pass

    new_process = subprocess.Popen([sys.executable] + sys.argv)
    print(f"New process started with PID: {new_process.pid}")

    time.sleep(1)
    os._exit(0)


def quit_program():
    QCoreApplication.exit()