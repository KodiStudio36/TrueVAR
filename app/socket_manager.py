import socketio
from PyQt5.QtCore import QObject, pyqtSignal
from app.main_manager import MainManager
from app.fight_manager import FightManager
from app.injector import singleton, Injector
from config import socketio_url

@singleton
class SocketManager(QObject):
    connected = pyqtSignal(bool)
    tournaments_received = pyqtSignal(list)
    tournament_data_received = pyqtSignal(dict)
    message_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.hub = Injector.find(MainManager)
        self.fight_manager = Injector.find(FightManager)
        self.socket_url = socketio_url
        self.license_key = None  # Stored here for authorized emits
        
        self.sio = socketio.Client(reconnection=True, reconnection_attempts=5)
        self._setup_handlers()

        self.hub.new_fight_signal.connect(self.new_fight)
        self.hub.update_fight_data_signal.connect(self.update_fight_data)
        self.hub.start_fight_signal.connect(self.start_fight)

    def _setup_handlers(self):
        @self.sio.event
        def connect():
            print(f"[SocketIO] Connected to {self.socket_url}")
            self.connected.emit(True)

        @self.sio.event
        def disconnect():
            print("[SocketIO] Disconnected")
            self.connected.emit(False)

        @self.sio.on("tournaments_list")
        def on_tournaments(data):
            names = data.get("tournaments", [])
            self.tournaments_received.emit(names)

        @self.sio.on("tournament_data")
        def on_data(data):
            self.hub.on_tournament_data_signal.emit(data["data"])
            self.tournament_data_received.emit(data)

        @self.sio.on("start_livestream")
        def start_livestream(data):
            self.hub.start_livestream_signal.emit()

        @self.sio.on("stop_livestream")
        def stop_livestream(data):
            self.hub.stop_livestream_signal.emit()

        @self.sio.on("start_tournament")
        def start_tournament(data):
            self.hub.start_tournament_signal.emit()

        @self.sio.on("stop_tournament")
        def stop_tournament(data):
            self.hub.stop_tournament_signal.emit()

        @self.sio.on("other_fight_started")
        def other_fight_started(data):
            self.hub.other_fight_started_signal.emit()

        @self.sio.event
        def connect_error(data):
            print(f"[SocketIO] Connection failed: {data}")

    def connect(self, token, license_key):
        """Initializes connection with the specific auth token."""
        self.license_key = license_key
        if self.sio.connected:
            self.sio.disconnect()
        
        try:
            self.sio.connect(self.socket_url, auth={'token': token}, wait_timeout=10)
        except Exception as e:
            print(f"[SocketIO] Connection error: {e}")

    def emit_authorized(self, event, payload):
        """Wraps emits to include the license key."""
        if not self.sio.connected or not self.license_key:
            print(f"[SocketIO] Cannot emit '{event}': Not ready.")
            return False

        payload["license_key"] = self.license_key
        self.sio.emit(event, payload)
        return True

    def select_tournament(self, tournament_name):
        self.emit_authorized("select_tournament", {"tournament_name": tournament_name})

    def new_fight(self):
        self.emit_authorized("new_fight", {"data": self.fight_manager.to_json()})

    def update_fight_data(self):
        self.emit_authorized("update_fight_data", {"data": self.fight_manager.to_json()})

    def start_fight(self):
        self.emit_authorized("start_fight", {})

    def disconnect(self):
        self.sio.disconnect()