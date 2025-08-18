# main.py
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt

# Import your manager and worker classes
from app.webserver_manager import WebServerManager

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyQt5 Server Controller')
        self.setGeometry(100, 100, 400, 200)

        self.manager = WebServerManager()

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        layout = QVBoxLayout()

        self.status_label = QLabel("Servers are stopped.")
        layout.addWidget(self.status_label)

        self.start_button = QPushButton('Start Servers')
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop Servers')
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

    def _setup_connections(self):
        print("llll")
        self.start_button.clicked.connect(self.manager.start_servers)
        self.stop_button.clicked.connect(self.manager.stop_servers)

    def closeEvent(self, event):
        # Ensure servers are stopped gracefully on app exit
        self.manager.stop_servers()
        event.accept()

if __name__ == '__main__':
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(qt_app.exec_())