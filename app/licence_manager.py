# app/licence_manager.py
import os
import requests  # You must run 'pip install requests'
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from app.injector import singleton
from app.settings_manager import SettingsManager, Setting
# NOTE: Add 'licence_settings_file' to your config.py
from config import licence_settings_file

# --- Worker Object ---
# This worker will live on a separate thread and
# handle all blocking network (requests) calls.
class ApiWorker(QObject):
    """Performs API requests in a separate thread."""
    
    # Signals to emit results back to the manager
    status_checked = pyqtSignal(dict)
    stream_started = pyqtSignal()
    stream_stopped = pyqtSignal()
    fight_message_sent = pyqtSignal(dict)
    api_error = pyqtSignal(str)  # To send error messages back

    def __init__(self):
        super().__init__()

    def _get_headers(self, licence_key):
        """Helper to create authentication headers."""
        if not licence_key:
            # Handle error gracefully if key is missing
            self.api_error.emit("Licence Key is not set.")
            return None
        return {
            'Authorization': f'Licence {licence_key}'
        }

    # --- Slots ---
    # These slots will be triggered by signals from the LicenceManager
    
    def check_stream_status(self, base_url, licence_key):
        try:
            headers = self._get_headers(licence_key)
            if headers is None: return
            
            # NOTE: Assumes your blueprint is registered at /api
            url = f"{base_url}/api/licence/stream/check" 
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                self.status_checked.emit(response.json())
            else:
                self.api_error.emit(response.json().get("error", "Unknown API error"))
        except Exception as e:
            self.api_error.emit(f"Connection error: {e}")

    def start_stream(self, base_url, licence_key):
        try:
            headers = self._get_headers(licence_key)
            if headers is None: return

            url = f"{base_url}/api/licence/stream/start"
            response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.stream_started.emit()
            else:
                self.api_error.emit(response.json().get("error", "Unknown API error"))
        except Exception as e:
            self.api_error.emit(f"Connection error: {e}")

    def stop_stream(self, base_url, licence_key):
        try:
            headers = self._get_headers(licence_key)
            if headers is None: return

            url = f"{base_url}/api/licence/stream/stop"
            response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.stream_stopped.emit()
            else:
                self.api_error.emit(response.json().get("error", "Unknown API error"))
        except Exception as e:
            self.api_error.emit(f"Connection error: {e}")

    def send_fight_message(self, base_url, licence_key, message):
        try:
            headers = self._get_headers(licence_key)
            if headers is None: return

            url = f"{base_url}/api/licence/stream/fight"
            payload = {"message": message}
            response = requests.put(url, headers=headers, json=payload, timeout=5)
            
            if response.status_code == 200:
                self.fight_message_sent.emit(response.json())
            else:
                self.api_error.emit(response.json().get("error", "Unknown API error"))
        except Exception as e:
            self.api_error.emit(f"Connection error: {e}")


@singleton
class LicenceManager(SettingsManager, QObject):
    """
    Manages API communication with the server using a licence key.
    Handles all requests in a separate thread to avoid blocking the UI.
    """
    
    # --- Public Signals for UI ---
    # These signals are forwarded from the worker for the UI to connect to.
    status_checked = pyqtSignal(dict)
    stream_started = pyqtSignal()
    stream_stopped = pyqtSignal()
    fight_message_sent = pyqtSignal(dict)
    api_error = pyqtSignal(str)

    # --- Internal Signals for Worker ---
    # These signals trigger the worker's slots.
    _check_stream_status = pyqtSignal(str, str)
    _start_stream = pyqtSignal(str, str)
    _stop_stream = pyqtSignal(str, str)
    _send_fight_message = pyqtSignal(str, str, str)

    # --- Settings ---
    api_base_url = Setting("http://127.0.0.1:8000") # Your Flask server URL
    licence_key = Setting("")                     # The licence key to authenticate

    def __init__(self):
        SettingsManager.__init__(self, licence_settings_file) 
        QObject.__init__(self) 
        
        self.thread = QThread()
        self.worker = ApiWorker()
        self.worker.moveToThread(self.thread)

        self._connect_signals()
        
        self.thread.start()
        print("LicenceManager started, API worker thread is running.")

    def _connect_signals(self):
        # Connect internal manager signals to worker slots
        self._check_stream_status.connect(self.worker.check_stream_status)
        self._start_stream.connect(self.worker.start_stream)
        self._stop_stream.connect(self.worker.stop_stream)
        self._send_fight_message.connect(self.worker.send_fight_message)

        # Connect worker result signals to manager's public signals (for UI)
        self.worker.status_checked.connect(self.status_checked.emit)
        self.worker.stream_started.connect(self.stream_started.emit)
        self.worker.stream_stopped.connect(self.stream_stopped.emit)
        self.worker.fight_message_sent.connect(self.fight_message_sent.emit)
        self.worker.api_error.connect(self.api_error.emit)

    # --- Public API Methods ---
    # These are the methods your UI (or other managers) will call.

    def check_stream_status(self):
        """Asynchronously checks the stream status on the server."""
        print("Requesting stream status check...")
        self._check_stream_status.emit(self.api_base_url, self.licence_key)

    def start_stream(self):
        """Asynchronously requests the server to start the broadcast."""
        print("Requesting stream start...")
        self._start_stream.emit(self.api_base_url, self.licence_key)

    def stop_stream(self):
        """Asynchronously requests the server to stop the broadcast."""
        print("Requesting stream stop...")
        self._stop_stream.emit(self.api_base_url, self.licence_key)

    def send_fight_message(self, message: str):
        """Asynchronously sends a new fight message to the server's live chat."""
        if not message:
            self.api_error.emit("Cannot send empty message.")
            return
        print(f"Requesting to send fight message: {message}")
        self._send_fight_message.emit(self.api_base_url, self.licence_key, message)

    # --- Settings Methods ---
    
    def set_licence_key(self, key: str):
        """Sets and saves the licence key."""
        self.licence_key = key.strip()
        print(f"Licence key set.")

    def set_api_base_url(self, url: str):
        """Sets and saves the API base URL."""
        self.api_base_url = url.strip()
        print(f"API base URL set to {self.api_base_url}")
        
    def stop_worker_thread(self):
        """Stops the worker thread. Call this on application exit."""
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
            print("LicenceManager API worker thread stopped.")