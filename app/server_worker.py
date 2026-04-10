# app/server_worker.py
import os
from flask import Flask, render_template
from flask_socketio import SocketIO
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class ServerWorker(QObject):
    """
    Handles the Flask and SocketIO server in a separate thread.
    Strictly handles data broadcasting to the frontend (Scoreboard).
    """
    def __init__(self, host="0.0.0.0", port=8000):
        super().__init__()
        self.host = host
        self.port = port
        self._is_running = False
        self.flask_app = None
        self.socketio = None

    def start_server(self):
        if self._is_running:
            return

        self._is_running = True
        print(f"Starting Web Server on port {self.port}...")

        # Initialize Flask
        self.flask_app = Flask(__name__)
        # Adjust paths if your folder structure differs
        self.flask_app.template_folder = os.path.join(os.getcwd(), 'server/templates')
        self.flask_app.static_folder = os.path.join(os.getcwd(), 'server/static')
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.flask_app, cors_allowed_origins="*", async_mode='threading')

        self._setup_routes()

        # Run the server
        # allow_unsafe_werkzeug is needed because we are running inside a PyQt thread
        self.socketio.run(self.flask_app, host=self.host, port=self.port, allow_unsafe_werkzeug=True)

    def stop_server(self):
        """Stops the SocketIO server."""
        if self._is_running and self.socketio:
            print("Stopping Web Server...")
            self.socketio.stop()
            self._is_running = False

    def listener_update(self, data):
        """Receives data from UDPManager (via WebServerManager) and sends to Browser."""
        if self.socketio and self._is_running:
            self.socketio.emit("listener_update", data)

    def show_next_round_widget(self):
        if self.socketio and self._is_running:
            self.socketio.emit("show_next_round", None)

    def hide_next_round_widget(self):
        if self.socketio and self._is_running:
            self.socketio.emit("hide_next_round", None)

    def show_fighter_bars_widget(self):
        if self.socketio and self._is_running:
            self.socketio.emit("show_fighter_bars", None)

    def hide_fighter_bars_widget(self):
        if self.socketio and self._is_running:
            self.socketio.emit("hide_fighter_bars", None)

    def show_ivr_widget(self):
        if self.socketio and self._is_running:
            self.socketio.emit("show_ivr", None)

    def hide_ivr_widget(self):
        if self.socketio and self._is_running:
            self.socketio.emit("hide_ivr", None)

    def show_round_results_widget(self):
        if self.socketio and self._is_running:
            self.socketio.emit("show_round_results", None)

    def hide_round_results_widget(self):
        if self.socketio and self._is_running:
            self.socketio.emit("hide_round_results", None)

    def show_win_widget(self):
        if self.socketio and self._is_running:
            self.socketio.emit("show_win", None)

    def hide_win_widget(self):
        if self.socketio and self._is_running:
            self.socketio.emit("hide_win", None)

    def reset_widgets(self, data):
        if self.socketio and self._is_running:
            self.socketio.emit("reset_widgets", {"event": "reset", "data": data})

    def _setup_routes(self):
        @self.flask_app.route('/')
        def index():
            return "TrueVAR Scoreboard Server Running..."

        @self.flask_app.route("/scoreboard")
        def scoreboard():
            return render_template("aaa.html")

        # @self.flask_app.route("/scoreboard")
        # def scoreboard():
        #     return render_template("scoreboard.html")

        # @self.flask_app.route("/bottom")
        # def bottom_nav():
        #     return render_template("stats.html")