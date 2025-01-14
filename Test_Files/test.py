import sys
import threading
import time

from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PyQt6.QtCore import QTimer

# Define the main window class
class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 Simple Example")
        self.setGeometry(100, 100, 300, 200)

        # Create a button and connect it to the slot method
        self.button = QPushButton("Exit", self)
        self.button.clicked.connect(self.on_button_click)

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)

        # Start the daemon thread
        self.start_daemon_thread()

        # Set up the timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_timeout)
        self.timer.start(2000)  # Timer triggers every 2000 milliseconds (2 seconds)

    def on_button_click(self):
        # Exit the application when the button is clicked
        QApplication.quit()

    def on_timer_timeout(self):
        # This method is called every time the timer times out
        print("Timer triggered!")

    def daemon_task(self):
        # This is the task that will run in the background thread
        while True:
            print("Daemon thread is running...")
            time.sleep(2)  # Sleep for 2 seconds before repeating

    def start_daemon_thread(self):
        # Create and start the daemon thread
        daemon_thread = threading.Thread(target=self.daemon_task, daemon=True)
        daemon_thread.start()


if __name__ == '__main__':
    # Create the application object
    app = QApplication(sys.argv)

    # Create an instance of the window
    window = MyWindow()
    window.show()

    # Start the application's event loop
    sys.exit(app.exec())
