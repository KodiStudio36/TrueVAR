# app/udp_manager.py
import os
import json
from PyQt5.QtCore import QThread, QObject, pyqtSignal

from app.udp_worker import UdpWorker
from config import udp_settings_file # NOTE: Add 'udp_settings_file = "config/udp.json"' to your config.py
from app.injector import Injector
from app.main_manager import MainManager
from app.injector import singleton

@singleton
class UdpManager(QObject):
    """Manages the UDP listener thread and settings."""
    # Signal to forward parsed UDP messages from the worker
    message_parsed = pyqtSignal(dict)
    # Signal to update UI about the listener's state (running/stopped)
    listener_state_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.udp_port = 9998
        self.thread = QThread()
        self.worker = None
        self.load_settings()

    def start_listener(self):
        if self.thread.isRunning():
            print("UDP listener is already running.")
            return

        self.thread = QThread()
        self.worker = UdpWorker(self.udp_port)
        self.worker.moveToThread(self.thread)

        # Connect signals between manager and worker
        self.screen_manager: MainManager = Injector.find(MainManager)

        self.thread.started.connect(self.worker.start_listener)
        self.worker.message_parsed.connect(self.message_parsed.emit) # Directly forward the signal
        self.worker.fight_started.connect(self.screen_manager.start_recording) # Directly forward the signal
        self.worker.fight_stopped.connect(self.screen_manager.stop_recording) # Directly forward the signal
        self.thread.finished.connect(self.on_listener_stopped)

        self.thread.start()
        self.listener_state_changed.emit(True)
        print(f"UDP Listener thread started for port {self.udp_port}.")

    def stop_listener(self):
        if self.thread.isRunning() and self.worker:
            self.worker.stop_listener()
            self.thread.quit()
            self.thread.wait()
        
    def on_listener_stopped(self):
        print("UDP Listener thread finished.")
        self.listener_state_changed.emit(False)

    def set_port(self, port):
        try:
            self.udp_port = int(port)
            self.save_settings()
            print(f"UDP port set to {self.udp_port}")
        except (ValueError, TypeError):
            print(f"Invalid port number: {port}")

    def save_settings(self):
        data = {"udp_port": self.udp_port}
        with open(udp_settings_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_settings(self):
        if os.path.exists(udp_settings_file):
            try:
                with open(udp_settings_file, 'r') as f:
                    data = json.load(f)
                    self.udp_port = data.get("udp_port", 9998)
            except (json.JSONDecodeError, KeyError):
                self.save_settings()
        else:
            self.save_settings()