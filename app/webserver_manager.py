# app/webserver_manager.py
import os
import json
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

from app.server_worker import ServerWorker
from config import webserver_settings_file

class WebServerManager(QObject):
    # Internal signal to pass data to the worker thread safely
    _broadcast_signal = pyqtSignal(dict)
    # Signal to update the UI about the server's state
    server_state_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        # self.udp_port = 9998 # REMOVED
        self.webserver_port = 8000
        self.obs_port = 4455
        self.obs_pass = "samko211"

        self.thread = QThread()
        self.worker = None

        self.load_webserver()

    def start_servers(self):
        if self.thread.isRunning():
            print("Servers are already running.")
            return

        self.thread = QThread()
        self.worker = ServerWorker(self)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.start_servers)
        self.thread.finished.connect(self.on_server_stopped) # Cleanly handle thread stop
        
        # Connect the broadcast signal to the worker's slot
        self._broadcast_signal.connect(self.worker.broadcast_data)

        self.thread.start()
        self.server_state_changed.emit(True)

    def stop_servers(self):
        if self.thread.isRunning():
            if self.worker:
                self.worker.stop_servers()
            self.thread.quit()
            self.thread.wait()

    def on_server_stopped(self):
        self.server_state_changed.emit(False)

    @pyqtSlot(dict)
    def receive_udp_data(self, data):
        """Public slot to receive data from UdpManager and forward to the worker."""
        if self.worker and self.thread.isRunning():
            self._broadcast_signal.emit(data)

    def save_webserver(self):
        """Save settings to a JSON file."""
        data = {
            # "udp_port": self.udp_port, # REMOVED
            "webserver_port": self.webserver_port,
            "obs_port": self.obs_port,
            "obs_pass": self.obs_pass,
        }
        with open(webserver_settings_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_webserver(self):
        """Load settings from a JSON file."""
        if os.path.exists(webserver_settings_file):
            with open(webserver_settings_file, 'r') as f:
                data = json.load(f)
                # self.udp_port = data["udp_port"] # REMOVED
                self.webserver_port = data.get("webserver_port", 8000)
                self.obs_port = data.get("obs_port", 4455)
                self.obs_pass = data.get("obs_pass", "samko211")
        else:
            self.save_webserver()

    def go_to_main_scene(self):
        if self.worker:
            self.worker.go_to_main_scene()

    def start_ivr_scene(self):
        if self.worker:
            self.worker.start_ivr_scene()

    def end_ivr_scene(self):
        if self.worker:
            self.worker.end_ivr_scene()
