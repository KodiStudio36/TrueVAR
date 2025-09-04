import os, json
from PyQt5.QtCore import QThread, QObject

from app.server_worker import ServerWorker
from config import webserver_settings_file
from app.injector import singleton
from app.settings_manager import SettingsManager, Setting

@singleton
class WebServerManager(SettingsManager):
    udp_port = Setting(9998)
    webserver_port = Setting(8000)
    obs_port = Setting(4455)
    obs_pass = Setting("samko211")

    def __init__(self):
        self.thread = QThread()
        self.worker = None

        super().__init__(webserver_settings_file)

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

    def start_ivr_scene(self):
        if self.worker:
            self.worker.start_ivr_scene()

    def end_ivr_scene(self):
        if self.worker:
            self.worker.end_ivr_scene()
