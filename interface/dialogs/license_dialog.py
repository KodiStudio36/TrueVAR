# interface/dialogs/license_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

class LicenseDialog(QDialog):
    def __init__(self, license_manager, parent=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.setWindowTitle("TrueVAR Activation")
        self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint) # No close button
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.info_label = QLabel("Please enter your license key to proceed.")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        layout.addWidget(self.key_input)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red")
        layout.addWidget(self.status_label)

        self.activate_btn = QPushButton("Activate")
        self.activate_btn.clicked.connect(self.on_activate)
        layout.addWidget(self.activate_btn)

        # Quit button in case they want to give up
        self.quit_btn = QPushButton("Exit")
        self.quit_btn.clicked.connect(self.reject)
        layout.addWidget(self.quit_btn)

        self.setLayout(layout)

    def on_activate(self):
        key = self.key_input.text().strip()
        if not key:
            self.status_label.setText("Key cannot be empty.")
            return

        self.activate_btn.setEnabled(False)
        self.status_label.setText("Connecting to server...")
        self.status_label.setStyleSheet("color: blue")
        self.repaint() # Force UI update

        success, message = self.license_manager.activate(key)

        if success:
            # QMessageBox.information(self, "Success", "Activation successful!")
            self.accept()
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: red")
            self.activate_btn.setEnabled(True)