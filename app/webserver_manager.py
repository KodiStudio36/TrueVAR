# app/webserver_manager.py
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from app.server_worker import ServerWorker
from app.injector import singleton, Injector
from app.udp_manager import UdpManager
from config import webserver_settings_file
from app.settings_manager import SettingsManager, Setting

@singleton
class WebServerManager(SettingsManager, QObject):
    server_state_changed = pyqtSignal(bool)
    
    # Internal signal to pass data to the worker thread safely
    _broadcast_signal = pyqtSignal(dict)

    # --- Settings ---
    webserver_port = Setting(8000)

    def __init__(self):
        SettingsManager.__init__(self, webserver_settings_file)
        QObject.__init__(self)
        
        self.thread = QThread()
        self.worker = None

    def start_server(self):
        if self.thread.isRunning():
            print("Web Server is already running.")
            return

        # 1. Create Worker
        self.worker = ServerWorker(port=self.webserver_port)
        self.worker.moveToThread(self.thread)

        # 2. Wire Thread Signals
        self.thread.started.connect(self.worker.start_server)
        self.thread.finished.connect(self.worker.stop_server)

        # # 3. Wire Data Flow (UDP -> WebServer)
        # # We find the existing UDP Manager instance
        # self.udp_manager = Injector.find(UdpManager)
        
        # if self.udp_manager:
        #     # Connect UDP parsed messages to our internal broadcast signal
        #     self.udp_manager.message_parsed.connect(self._broadcast_signal.emit)
        #     # Connect internal signal to the worker's slot (Thread-Safe)
        #     self._broadcast_signal.connect(self.worker.broadcast_data)
        # else:
        #     print("WARNING: UdpManager not found. Scoreboard will not update.")

        # 4. Start
        self.thread.start()
        self.server_state_changed.emit(True)
        print(f"WebServerManager started on port {self.webserver_port}")

    def show_ivr_widget(self):
        if self.worker:
            self.worker.show_ivr()

    def hide_ivr_widget(self):
        if self.worker:
            self.worker.hide_ivr()

    def stop_server(self):
        if self.thread.isRunning():
            if self.worker:
                self.worker.stop_server()
            self.thread.quit()
            self.thread.wait()
            self.server_state_changed.emit(False)
            print("WebServerManager stopped.")