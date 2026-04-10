import json
import hashlib
import platform
import uuid
import time
import os
import requests
from PyQt5.QtCore import QObject, pyqtSignal
from app.injector import singleton
from config import licence_settings_file, api_fetch_url

@singleton
class LicenseManager(QObject):
    # Signals the UI and the SocketManager
    license_status_changed = pyqtSignal(bool, str)
    # New signal: (socket_token, license_key)
    connection_ready = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.license_file = licence_settings_file
        self.api_url = api_fetch_url
        
        self.current_blob = None
        self.machine_id = self._generate_machine_id()

    def validate(self):
        """Returns True if license is valid (online or offline)."""
        local_valid = self._load_and_verify_local()
        online_success = self._fetch_online_status()

        if online_success:
            self.license_status_changed.emit(True, "Online Verified")
            return True
        elif local_valid:
            expires_at = self.current_blob['data']['expires_at']
            if time.time() < expires_at:
                self.license_status_changed.emit(True, "Offline Verified")
                return True
        
        self.license_status_changed.emit(False, "Invalid License")
        return False

    def activate(self, license_key):
        try:
            payload = {
                "license_key": license_key,
                "machine_id": self.machine_id,
                "app_version": "1.0.0",
                "client_time": int(time.time())
            }
            response = requests.post(self.api_url, json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    self.current_blob = data["license_blob"]
                    self._save_blob(self.current_blob)
                    
                    # Signal that we are ready to connect to SocketIO
                    token = data["socketio"]["token"]
                    key = data["license_blob"]["data"]["license_key"]
                    self.connection_ready.emit(token, key)
                    
                    self.license_status_changed.emit(True, "Activated Successfully")
                    return True, "Activated"
            return False, "Activation Failed"
        except Exception as e:
            return False, str(e)

    def _generate_machine_id(self):
        info = [platform.node(), platform.machine(), str(uuid.getnode())]
        return hashlib.sha256("".join(info).encode()).hexdigest()

    def _fetch_online_status(self):
        if not self.current_blob: return False
        try:
            key = self.current_blob['data']['license_key']
            payload = {"license_key": key, "machine_id": self.machine_id, "app_version": "1.0.0"}
            response = requests.post(self.api_url, json=payload, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    self.current_blob = data["license_blob"]
                    self._save_blob(self.current_blob)
                    
                    # Signal for SocketIO reconnect
                    self.connection_ready.emit(data["socketio"]["token"], key)
                    return True
            return False
        except:
            return False

    def _load_and_verify_local(self):
        if not os.path.exists(self.license_file): return False
        try:
            with open(self.license_file, 'r') as f:
                blob = json.load(f)
            if blob.get('data', {}).get('machine_id') == self.machine_id:
                self.current_blob = blob
                return True
        except: pass
        return False

    def _save_blob(self, blob):
        with open(self.license_file, 'w') as f:
            json.dump(blob, f)

    # Add this inside your LicenseManager class

    def check_reachability(self):
        """Checks server and validates license for Online Mode."""
        try:
            # 1. Ping the server
            requests.head(self.api_url, timeout=5)
            
            # 2. Check if we have a license to actually use the online features
            local_exists = self._load_and_verify_local()
            if local_exists:
                # Validate online to get the fresh SocketIO token
                return self._fetch_online_status() 
            
            return False # Reachable, but no license = can't go online
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return False # Server unreachable