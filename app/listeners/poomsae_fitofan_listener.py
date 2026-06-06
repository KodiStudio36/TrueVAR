# app/poomsae_fitofan_listener.py
from PyQt5.QtCore import QThread, pyqtSignal
from app.listeners.base_listener import BaseListener
from app.listeners.poomsae_fitofan_worker import PoomsaeFitofanWorker
from config import poomsae_fitofan_settings_file
from app.settings_manager import SettingsManager, Setting


class PoomsaeFitofanListener(SettingsManager, BaseListener):
    """
    Manages the poomsae WebSocket-proxy listener thread and its settings.

    Architecture:
        Browser  ──proxy──►  mitmproxy  (mitmproxy_poomsae_addon.py)
                                  │
                                  │  UDP datagrams  →  127.0.0.1:udp_port
                                  ▼
                         PoomsaeFitofanWorker
                                  │
                                  │  hub signals
                                  ▼
                            MainManager / overlay
    """

    listener_state_changed = pyqtSignal(bool)

    # Must match FORWARD_PORT in mitmproxy_poomsae_addon.py
    udp_port = Setting(9997)

    def __init__(self):
        SettingsManager.__init__(self, poomsae_fitofan_settings_file)
        BaseListener.__init__(self)
        self.thread = QThread()
        self.worker = None

    def start(self):
        if self.thread.isRunning():
            print("[Poomsae] Listener already running.")
            return
        self.thread = QThread()
        self.worker = PoomsaeFitofanWorker(self.udp_port)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start_listener)
        self.thread.finished.connect(self.on_listener_stopped)
        self.thread.start()
        self.listener_state_changed.emit(True)
        print(f"[Poomsae] Listener started on port {self.udp_port}.")

    def stop(self):
        if self.thread.isRunning() and self.worker:
            self.worker.stop_listener()
            self.thread.quit()
            self.thread.wait()

    def on_listener_stopped(self):
        print("[Poomsae] Listener stopped.")
        self.listener_state_changed.emit(False)

    def set_port(self, port):
        try:
            self.udp_port = int(port)
            print(f"[Poomsae] Port set to {self.udp_port}")
        except (ValueError, TypeError):
            print(f"[Poomsae] Invalid port: {port}")
