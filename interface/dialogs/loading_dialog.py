# interface/dialogs/loading_dialog.py
import time
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class NetworkCheckWorker(QThread):
    # Changed signal to 'object' to handle True, False, or "ACTIVATE"
    finished_check = pyqtSignal(object) 

    def __init__(self, license_manager):
        super().__init__()
        self.license_manager = license_manager

    def run(self):
        result = self.license_manager.check_reachability()
        self.finished_check.emit(result)

class StartupLoaderDialog(QDialog):
    def __init__(self, license_manager, parent=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.is_offline_mode = False
        self.needs_activation = False
        
        self.setWindowTitle("Connecting...")
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        layout = QVBoxLayout()
        self.label = QLabel("Establishing secure connection...")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0) 
        layout.addWidget(self.progress)
        self.setLayout(layout)

        self.worker = NetworkCheckWorker(self.license_manager)
        self.worker.finished_check.connect(self.on_check_done)

    def start_check(self):
        self.worker.start()

    def on_check_done(self, result):
        if result is True:
            self.accept() 
        elif result == "ACTIVATE":
            self.needs_activation = True
            self.accept()
        else:
            # Failed to connect or no license found
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Online Mode Unavailable")
            msg.setText("Could not connect to server or license missing.")
            msg.setInformativeText("Would you like to try again (Online) or continue for free (Offline)?")
            
            retry_btn = msg.addButton("Retry Online", QMessageBox.ActionRole)
            offline_btn = msg.addButton("Continue Offline", QMessageBox.AcceptRole)
            
            msg.exec_()
            
            if msg.clickedButton() == retry_btn:
                self.start_check()
            else:
                self.is_offline_mode = True
                self.accept() # Always allow offline