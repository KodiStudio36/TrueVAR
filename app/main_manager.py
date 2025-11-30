from PyQt5.QtCore import QObject, pyqtSignal
from app.injector import singleton

@singleton
class MainManager(QObject):
    show_settings_signal = pyqtSignal()
    hide_settings_signal = pyqtSignal()
    show_replay_signal = pyqtSignal()
    hide_replay_signal = pyqtSignal()
    toggle_recording_signal = pyqtSignal()
    start_recording_signal = pyqtSignal()
    stop_recording_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    def show_settings(self):
        self.show_settings_signal.emit()

    def hide_settings(self):
        self.hide_settings_signal.emit()

    def show_replay(self):
        self.show_replay_signal.emit()

    def hide_replay(self):
        self.hide_replay_signal.emit()

    def toggle_recording(self):
        self.toggle_recording_signal.emit()

    def start_recording(self):
        self.start_recording_signal.emit()

    def stop_recording(self):
        self.stop_recording_signal.emit()
