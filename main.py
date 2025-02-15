import sys
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication
from app.controller_manager import ControllerManager
from app.key_bind_manager import KeyBindManager
from app.camera_manager import CameraManager
from interface.main_window import MainWindow

from config import icon_file

def main():
    app = QApplication(sys.argv)

    # Initialize managers
    controller_manager = ControllerManager()
    controller_manager.start()
    
    key_bind_manager = KeyBindManager()
    camera_manager = CameraManager()

    # Create the main window with the stacked layout
    main_window = MainWindow(controller_manager, key_bind_manager, camera_manager)
    main_window.setWindowTitle("TrueVAR")
    main_window.setWindowIcon(QIcon(QPixmap(icon_file)))
    main_window.show()

    # Start the event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
