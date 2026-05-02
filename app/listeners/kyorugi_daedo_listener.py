# app/kyorugi_daedo_listener.py
from PyQt5.QtCore import QThread, pyqtSignal

from app.listeners.base_listener import BaseListener
from app.listeners.kyorugi_daedo_worker import KyorugiDaedoWorker
from config import kyorugi_daedo_settings_file
from app.settings_manager import SettingsManager, Setting

class KyorugiDaedoListener(SettingsManager, BaseListener):
    """Manages the UDP listener thread and settings."""
    listener_state_changed = pyqtSignal(bool)

    udp_port = Setting(9998)

    def __init__(self):
        SettingsManager.__init__(self, kyorugi_daedo_settings_file) 
        BaseListener.__init__(self) 

        self.thread = QThread()
        self.worker = None

    def start(self):
        if self.thread.isRunning():
            print("UDP listener is already running.")
            return

        self.thread = QThread()

        self.worker = KyorugiDaedoWorker(self.udp_port) 
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.start_listener)
        self.thread.finished.connect(self.on_listener_stopped)

        self.thread.start()
        self.listener_state_changed.emit(True)
        print(f"UDP Listener thread started for port {self.udp_port}.")

    def stop(self):
        if self.thread.isRunning() and self.worker:
            self.worker.stop_listener()
            self.thread.quit()
            self.thread.wait()
        
    def on_listener_stopped(self):
        print("UDP Listener thread finished.")
        self.listener_state_changed.emit(False)

    def set_port(self, port):
        """Sets the UDP port. The value is automatically saved."""
        try:
            self.udp_port = int(port)
            print(f"UDP port set to {self.udp_port}")
        except (ValueError, TypeError):
            print(f"Invalid port number: {port}")