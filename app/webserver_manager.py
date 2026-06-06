# app/webserver_manager.py
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from app.server_worker import ServerWorker
from app.injector import singleton, Injector
from config import webserver_settings_file
from app.settings_manager import SettingsManager, Setting
from app.main_manager import MainManager

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

        # 4. Start
        self.thread.start()
        self.server_state_changed.emit(True)
        print(f"WebServerManager started on port {self.webserver_port}")

        self.hub = Injector.find(MainManager)
        self.hub.listener_stable_signal.connect(self.listener_update)

    def show_clock_widget(self):
        if self.worker:
            self.worker.show_clock_widget()

    def hide_clock_widget(self):
        if self.worker:
            self.worker.hide_clock_widget()

    def show_next_round_widget(self):
        if self.worker:
            self.worker.show_next_round_widget()

    def hide_next_round_widget(self):
        if self.worker:
            self.worker.hide_next_round_widget()

    def show_fighter_bars_widget(self):
        if self.worker:
            self.worker.show_fighter_bars_widget()

    def hide_fighter_bars_widget(self):
        if self.worker:
            self.worker.hide_fighter_bars_widget()

    def show_ivr_widget(self):
        if self.worker:
            self.worker.show_ivr_widget()

    def hide_ivr_widget(self):
        if self.worker:
            self.worker.hide_ivr_widget()

    def show_round_results_widget(self):
        if self.worker:
            self.worker.show_round_results_widget()

    def hide_round_results_widget(self):
        if self.worker:
            self.worker.hide_round_results_widget()

    def show_win_widget(self):
        if self.worker:
            self.worker.show_win_widget()

    def hide_win_widget(self):
        if self.worker:
            self.worker.hide_win_widget()

    def show_yt_widget(self):
        if self.worker:
            self.worker.show_yt_widget()

    def hide_yt_widget(self):
        if self.worker:
            self.worker.hide_yt_widget()

    def show_ticker_widget(self, data):
        if self.worker:
            self.worker.show_ticker_widget(data)

    def reset_widgets(self, data=None):
        if self.worker:
            self.worker.reset_widgets(data)    

    def listener_update(self, data):
        if self.worker:
            self.worker.listener_update(data)

    def stop_server(self):
        if self.thread.isRunning():
            if self.worker:
                self.worker.stop_server()
            self.thread.quit()
            self.thread.wait()
            self.server_state_changed.emit(False)
            print("WebServerManager stopped.")