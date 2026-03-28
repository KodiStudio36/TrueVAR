# interface/dialogs/tournament_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QSpinBox
from PyQt5.QtCore import Qt

class TournamentSelectionDialog(QDialog):
    def __init__(self, tournaments, max_courts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Tournament & Court")
        self.setFixedSize(320, 200)
        
        layout = QVBoxLayout()
        
        # Tournament Selection
        layout.addWidget(QLabel("Select Tournament:"))
        self.combo = QComboBox()
        self.combo.addItems(tournaments)
        layout.addWidget(self.combo)
        
        layout.addSpacing(10)
        
        # Court Selection
        layout.addWidget(QLabel(f"Assign to Court (1 - {max_courts}):"))
        self.court_spin = QSpinBox()
        self.court_spin.setRange(1, max_courts)
        self.court_spin.setValue(1)
        layout.addWidget(self.court_spin)
        
        layout.addStretch()
        
        self.btn = QPushButton("Confirm Selection")
        self.btn.clicked.connect(self.accept)
        layout.addWidget(self.btn)
        
        self.setLayout(layout)

    def get_selection(self):
        """Returns a tuple of (name, court_number)"""
        return self.combo.currentText(), self.court_spin.value()