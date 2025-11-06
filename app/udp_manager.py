# app/udp_manager.py
import os
from PyQt5.QtCore import QThread, QObject, pyqtSignal

from app.udp_worker import UdpWorker
from config import udp_settings_file # NOTE: Add 'udp_settings_file = "config/udp.json"' to your config.py
from app.injector import Injector
from app.main_manager import MainManager
from app.injector import singleton
from app.settings_manager import SettingsManager, Setting # <-- Import new base class/descriptor

@singleton
class UdpManager(SettingsManager, QObject): # <-- Inherit from QObject (first) and SettingsManager
    """Manages the UDP listener thread and settings."""
    # Signal to forward parsed UDP messages from the worker
    message_parsed = pyqtSignal(dict)
    # Signal to update UI about the listener's state (running/stopped)
    listener_state_changed = pyqtSignal(bool)

    # --- Settings ---
    # Define settings using the descriptor. This replaces manual load/save.
    udp_port = Setting(9998) 
    udp_default = Setting(False) 

    def __init__(self):
        # Call QObject init first
        SettingsManager.__init__(self, udp_settings_file) 
        QObject.__init__(self) 
        # Then call SettingsManager init, which loads settings

        self.thread = QThread()
        self.worker = None
        # self.load_settings() <-- No longer needed

    def start_listener(self):
        if self.thread.isRunning():
            print("UDP listener is already running.")
            return

        self.thread = QThread()
        # self.udp_port is now correctly fetched via the Setting descriptor
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
        """Sets the UDP port. The value is automatically saved."""
        try:
            # Assigning to self.udp_port triggers the Setting descriptor's
            # __set__ method, which handles type validation (if any)
            # and automatically calls self.save()
            self.udp_port = int(port)
            print(f"UDP port set to {self.udp_port}")
        except (ValueError, TypeError):
            print(f"Invalid port number: {port}")
        # self.save_settings() <-- No longer needed

    # save_settings() and load_settings() are removed, 
    # as they are handled by the SettingsManager base class.