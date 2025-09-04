import sys, os
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication
from interface.main_window import MainWindow

from config import records_path, settings_path

def main():
    app = QApplication(sys.argv)

    os.makedirs(records_path, exist_ok=True)
    os.makedirs(settings_path, exist_ok=True)

    # Create the main window with the stacked layout
    main_window = MainWindow()
    main_window.setWindowTitle("TrueVAR")
    main_window.show()

    # Start the event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
