from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt

class MyLineEdit(QLineEdit):
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape):
            self.clearFocus()  # Remove focus
        else:
            super().keyPressEvent(event)