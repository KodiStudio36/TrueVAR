from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QSpinBox
from PyQt5.QtCore import Qt

class TournamentSelectionDialog(QDialog):
    def __init__(self, tournament_data, parent=None):
        """
        :param tournament_data: A dictionary like {"Tournament A": 4, "Tournament B": 8}
        """
        super().__init__(parent)
        self.tournament_map = tournament_data
        self.tournament_names = list(tournament_data.keys())

        self.setWindowTitle("Select Tournament & Court")
        self.setFixedSize(320, 220)
        
        layout = QVBoxLayout()
        
        # 1. Tournament Selection
        layout.addWidget(QLabel("Select Tournament:"))
        self.combo = QComboBox()
        self.combo.addItems(self.tournament_names)
        # Connect the change event
        self.combo.currentTextChanged.connect(self.update_court_limit)
        layout.addWidget(self.combo)
        
        layout.addSpacing(10)
        
        # 2. Court Selection
        self.court_label = QLabel("Assign to Court:")
        layout.addWidget(self.court_label)
        
        self.court_spin = QSpinBox()
        # Initial setup based on first item
        self.update_court_limit(self.combo.currentText())
        layout.addWidget(self.court_spin)
        
        layout.addStretch()
        
        self.btn = QPushButton("Confirm Selection")
        self.btn.clicked.connect(self.accept)
        layout.addWidget(self.btn)
        
        self.setLayout(layout)

    def update_court_limit(self, tournament_name):
        """Updates the spinbox range whenever the tournament selection changes."""
        if not tournament_name:
            return

        # Get max courts from our mapping
        max_courts = self.tournament_map.get(tournament_name, 1)
        
        # Update the UI
        self.court_label.setText(f"Assign to Court (1 - {max_courts}):")
        self.court_spin.setRange(1, max_courts)
        
        # Optional: Reset value to 1 if the current value exceeds new max
        if self.court_spin.value() > max_courts:
            self.court_spin.setValue(1)

    def get_selection(self):
        """Returns a tuple of (name, court_number)"""
        return self.combo.currentText(), self.court_spin.value()