# app/key_bind_manager.py
import os, json
from PyQt5.QtCore import QThread, QObject

from app.server_worker import ServerWorker
from config import webserver_settings_file

class WebServerManager:
    def __init__(self):
        self.udp_port = 9998
        self.webserver_port = 8000
        self.obs_port = 4455
        self.obs_pass = "samko211"

        self.thread = QThread()
        self.worker = None

        self.load_webserver()

    def start_servers(self):
        print("ggggg")
        if self.thread.isRunning():
            print("Servers are already running.")
            return

        # Create QThread and Worker instances
        self.thread = QThread()
        self.worker = ServerWorker(self)
        
        # Move the worker to the thread
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.start_servers)

        self.worker.on_fight_start.connect(self.context.start_recording)
        self.worker.on_fight_stop.connect(self.context.stop_recording)

        # Start the thread
        self.thread.start()

    def stop_servers(self):
        if self.thread.isRunning():
            # Signal the worker to stop gracefully
            self.worker.stop_servers()
            # Wait for the thread to finish
            self.thread.wait()

    def set_context(self, context):
        self.context = context

    def go_to_main_scene(self):
        if self.worker:
            self.worker.go_to_main_scene()

    def go_to_ivr_scene(self):
        if self.worker:
            self.worker.go_to_ivr_scene()

    def save_webserver(self):
        """Save key binds to a JSON file."""
        data = {
            "udp_port": self.udp_port,
            "webserver_port": self.webserver_port,
            "obs_port": self.obs_port,
            "obs_pass": self.obs_pass,
        }
        with open(webserver_settings_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_webserver(self):
        """Load key binds from a JSON file."""
        if os.path.exists(webserver_settings_file):
            with open(webserver_settings_file, 'r') as f:
                data = json.load(f)
                self.udp_port = data["udp_port"]
                self.webserver_port = data["webserver_port"]
                self.obs_port = data["obs_port"]
                self.obs_pass = data["obs_pass"]
