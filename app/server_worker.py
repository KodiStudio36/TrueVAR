# app/server_worker.py
import os
from flask import Flask, render_template
from flask_socketio import SocketIO
from obswebsocket import obsws, requests
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class ServerWorker(QObject):
    # These signals are not used here, but kept for consistency if needed later
    on_fight_start = pyqtSignal()
    on_fight_stop = pyqtSignal()

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self._is_running = False
        self.flask_app = None
        self.socketio = None
        self.obs_ws = None

    def start_servers(self):
        if self._is_running:
            return

        self._is_running = True
        print("Starting web and OBS servers...")

        self.flask_app = Flask(__name__)
        self.flask_app.template_folder = os.path.join(os.getcwd(), 'server/templates')
        self.flask_app.static_folder = os.path.join(os.getcwd(), 'server/static')
        self.socketio = SocketIO(self.flask_app, cors_allowed_origins="*", async_mode='threading')

        self._setup_routes()

        try:
            self.obs_ws = obsws("localhost", self.manager.obs_port, self.manager.obs_pass)
            self.obs_ws.connect()
            print(f"Connected to OBS on port {self.manager.obs_port}")
        except Exception as e:
            print(f"Failed to connect to OBS: {e}")
            self.obs_ws = None
        
        print(f"Web server running on http://0.0.0.0:{self.manager.webserver_port}")
        # Use allow_unsafe_werkzeug for development compatibility with SocketIO's threading
        self.socketio.run(self.flask_app, host="0.0.0.0", port=self.manager.webserver_port, allow_unsafe_werkzeug=True)

        print("Web server has stopped.")
        self._cleanup()

    def stop_servers(self):
        if not self._is_running:
            return
        print("Stopping web server...")
        self._is_running = False
        self.socketio.stop()

    @pyqtSlot(dict)
    def broadcast_data(self, data):
        """Receives a parsed dictionary and broadcasts it via Socket.IO."""
        if self.socketio:
            self.socketio.emit("udp_message", data)

    def _cleanup(self):
        if self.obs_ws and self.obs_ws.is_connected():
            print("Disconnecting from OBS...")
            self.obs_ws.disconnect()
            self.obs_ws = None
        print("Web server connections are shut down.")

    def _setup_routes(self):
        @self.flask_app.route('/')
        def index():
            return "Server is running..."

        @self.flask_app.route("/scoreboard")
        def scoreboard():
            return render_template("scoreboard.html")

        @self.flask_app.route("/bottom")
        def bottom_nav():
            return render_template("stats.html")
    
    # --- OBS control methods remain unchanged ---
    def go_to_main_scene(self):
        if self.obs_ws:
            self.obs_ws.call(requests.SetCurrentProgramScene(sceneName="Main Scene")) 

    def start_ivr_scene(self):
        self.socketio.emit("udp_message", {"event": "IVRStart"})
        if self.obs_ws:
            self.obs_ws.call(requests.SetCurrentProgramScene(sceneName="IVR Scene")) 

    def end_ivr_scene(self):
        self.socketio.emit("udp_message", {"event": "IVREnd"})
        if self.obs_ws:
            self.obs_ws.call(requests.SetCurrentProgramScene(sceneName="Main Scene"))