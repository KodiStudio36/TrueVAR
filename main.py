import sys, os
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication
from app.key_bind_manager import KeyBindManager
from app.webserver_manager import WebServerManager
from app.camera_manager import CameraManager
from interface.main_window import MainWindow

from config import records_path, settings_path

def main():
    app = QApplication(sys.argv)

    os.makedirs(records_path, exist_ok=True)
    os.makedirs(settings_path, exist_ok=True)

    # Initialize managers
    key_bind_manager = KeyBindManager()
    webserver_manager = WebServerManager()
    camera_manager = CameraManager()

    # Create the main window with the stacked layout
    main_window = MainWindow(key_bind_manager, camera_manager, webserver_manager)
    main_window.setWindowTitle("TrueVAR")
    main_window.show()

    # Start the event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
