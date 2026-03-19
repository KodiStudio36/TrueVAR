# interface/dialogs/tournament_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton

class TournamentSelectionDialog(QDialog):
    def __init__(self, tournaments, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Tournament")
        self.setFixedSize(300, 150)
        self.selected_name = None
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Multiple tournaments found. Please select one:"))
        
        self.combo = QComboBox()
        self.combo.addItems(tournaments)
        layout.addWidget(self.combo)
        
        self.btn = QPushButton("Confirm")
        self.btn.clicked.connect(self.accept)
        layout.addWidget(self.btn)
        self.setLayout(layout)

    def get_selection(self):
        return self.combo.currentText()