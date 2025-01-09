from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QGraphicsOpacityEffect
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QTimer

class MainScreen(QWidget):
    def __init__(self, camera_manager):
        super().__init__()
        self.camera_manager = camera_manager
        self.blink_timers = {}  # To store timers for each camera's blink effect
        self.init_ui()

    def init_ui(self):
        self.layout = QGridLayout()

        # Recording status label
        status_label = QLabel()
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")  # Bold and larger text
        status_label.setText(f"TrueVAR is not recording")  # Initial status
        self.layout.addWidget(status_label, 1, 1)

        # Connect the camera's is_recording signal to update status label and start/stop blink
        self.camera_manager.is_recording_stream.connect(lambda is_recording, label=status_label:
                                    self.update_status(label, is_recording))

        # Set the main layout
        self.setLayout(self.layout)

    def update_status(self, label, is_recording):
        """Update the label color and blinking based on recording status."""
        if is_recording:
            label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            label.setText(f"TrueVAR is recording")
        else:
            label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            label.setText(f"TrueVAR is not recording")