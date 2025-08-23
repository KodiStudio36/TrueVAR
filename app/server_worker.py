# app/server_worker.py
# import eventlet
# eventlet.monkey_patch()

import sys
import os
import json
import threading
import socket
import atexit

from flask import Flask, render_template
from flask_socketio import SocketIO
from obswebsocket import obsws, requests

from PyQt5.QtCore import QObject, pyqtSignal

# Assume this file exists
from app.country import alpha3_to_alpha2

# === Global State Variables ===
# This is a bit messy, a better approach might be to
# encapsulate this state in a class, but for now, we'll keep it simple
# to match your original code.
update_data = {
    "event": "Update",
    "clk": "",
    "kye_shi": False,
    "brk": False,
    "match_id": 0,
    "title": "",
    "category": "",
    "hit_level": 0,
    "round": 1,
    "blue_name": "",
    "blue_flag": "",
    "blue_points_1": 0,
    "blue_points_2": 0,
    "blue_points_3": 0,
    "blue_gam_jeom": 0,
    "red_name": "",
    "red_flag": "",
    "red_points_1": 0,
    "red_points_2": 0,
    "red_points_3": 0,
    "red_gam_jeom": 0,
}

round_state = False
stream_started = False

class ServerWorker(QObject):

    on_fight_start = pyqtSignal()
    on_fight_stop = pyqtSignal()

    def __init__(self, manager):
        super().__init__()

        self.manager = manager
        self._is_running = False

        self.flask_app = None
        self.socketio = None
        self.udp_socket = None
        self.obs_ws = None
        self.udp_thread = None

    def start_servers(self):
        if self._is_running:
            return

        self._is_running = True
        print("Starting all servers...")

        # Initialize Flask
        self.flask_app = Flask(__name__)
        # Ensure templates folder exists for render_template to work
        # You might need to adjust this path based on your project structure
        self.flask_app.template_folder = os.path.join(os.getcwd(), 'server/templates')
        self.flask_app.static_folder = os.path.join(os.getcwd(), 'server/static')
        self.socketio = SocketIO(self.flask_app, cors_allowed_origins="*", async_mode='threading')

        # Dynamically set routes based on your original code
        self._setup_routes()

        # Connect to OBS
        try:
            self.obs_ws = obsws("localhost", self.manager.obs_port, self.manager.obs_pass)
            self.obs_ws.connect()
            print(f"Connected to OBS on port {self.manager.obs_port}")
        except Exception as e:
            print(f"Failed to connect to OBS: {e}")
            # Consider gracefully handling this or re-raising
            self.obs_ws = None

        # Start UDP listener in its own daemon thread
        self.socketio.start_background_task(self._udp_listener_loop)

        # Start the Flask server - this is the blocking call
        print(f"Web server running on http://0.0.0.0:{self.manager.webserver_port}")
        
        # This will block until the server is shut down
        self.socketio.run(self.flask_app, host="0.0.0.0", port=self.manager.webserver_port)

        print("Web server has stopped.")
        self._cleanup()

    def go_to_main_scene(self):
        if self.obs_ws:
            self.obs_ws.call(requests.SetCurrentProgramScene(sceneName="Main Scene")) 

    def start_ivr_scene(self):
        self.socketio.emit("udp_message", {
            "event": "IVRStart",
        })

        if self.obs_ws:
            self.obs_ws.call(requests.SetCurrentProgramScene(sceneName="IVR Scene")) 

    def end_ivr_scene(self):
        self.socketio.emit("udp_message", {
            "event": "IVREnd",
        })

        if self.obs_ws:
            self.obs_ws.call(requests.SetCurrentProgramScene(sceneName="Main Scene"))

    def stop_servers(self):
        if not self._is_running:
            return
        
        print("Stopping servers...")
        self._is_running = False
        
        # Stop the Flask server by emitting a 'shutdown' event
        # This is a common way to shut down a SocketIO server
        self.socketio.stop()

    def _cleanup(self):
        """Closes all connections."""
        if self.udp_socket:
            print("Closing UDP socket...")
            self.udp_socket.close()
            self.udp_socket = None
        
        if self.obs_ws and self.obs_ws.is_connected():
            print("Disconnecting from OBS...")
            self.obs_ws.disconnect()
            self.obs_ws = None
            
        print("All servers and connections are shut down.")


    # --- UDP Listener Logic (moved into the worker class) ---
    def _udp_listener_loop(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("0.0.0.0", self.manager.udp_port))
        print(f"[UDP Server] Listening on 0.0.0.0:{self.manager.udp_port}...")

        while self._is_running:
            try:
                data, addr = self.udp_socket.recvfrom(2048)
                message = data.decode(errors='ignore').strip()
                if not message:
                    continue

                print(f"[UDP] Received: {message} from {addr}")
                self._parse_udp_message(message)

                self.socketio.emit("udp_message", update_data)
            except socket.error as e:
                # Handle socket being closed while waiting for data
                if not self._is_running:
                    break
                print(f"[UDP Server] Socket Error: {e}")
            except Exception as e:
                print(f"[UDP Server] Error: {e}")

        if self.udp_socket:
            self.udp_socket.close()
            print("[UDP Server] UDP listener has stopped.")

    # --- Flask Routes and Parser Logic (moved into the worker class) ---
    def _setup_routes(self):
        # We need to set up the routes from within the Flask application's context
        @self.flask_app.route('/')
        def index():
            return "Server is running..."

        @self.flask_app.route("/scoreboard")
        def scoreboard():
            return render_template("scoreboard.html")

        @self.flask_app.route("/bottom")
        def bottom_nav():
            return render_template("stats.html")
            
        # You would also need to update the `@socketio.on` decorator if you use it

    def _parse_udp_message(self, msg: str):
        global round_state, clk, stream_started

        parts = msg.strip().split(";")
        if not parts:
            return None

        command = parts[0].lower()

        if command == "clk":
            # clk;01:20;stop or clk;01:20;start
            update_data["clk"] = parts[1][1:]
            clk = parts[1][1:]
            update_data["kye_shi"] = False
            update_data["brk"] = False

            if len(parts) > 2 and parts[2] == "start" and not round_state:
                self.socketio.emit("udp_message", {"event": "RoundStart"})
                round_state = True

                self.on_fight_start.emit()

                if not stream_started:
                    stream_started = False
                    self.go_to_main_scene()

        elif command == "ij0":
            # brk;[break_time]
            update_data["clk"] = parts[1][1:]
            update_data["kye_shi"] = True
            update_data["brk"] = False

            if len(parts) > 2 and parts[2] == "hide":
                update_data["clk"] = clk
                update_data["kye_shi"] = False

        elif command == "brk":
            # brk;[break_time]
            update_data["clk"] = parts[1][1:]
            update_data["kye_shi"] = False
            update_data["brk"] = True

            if round_state:
                self.socketio.emit("udp_message", {
                    "event": "RoundEnd",
                    "round": update_data["round"],
                    "blue_name": update_data["blue_name"],
                    "blue_flag": update_data["blue_flag"],
                    "red_name": update_data["red_name"],
                    "red_flag": update_data["red_flag"],
                    "blue_points_1": update_data["blue_points_1"],
                    "blue_points_2": update_data["blue_points_2"],
                    "blue_points_3": update_data["blue_points_3"],
                    "red_points_1": update_data["red_points_1"],
                    "red_points_2": update_data["red_points_2"],
                    "red_points_3": update_data["red_points_3"],
                })
                round_state = False
                update_data["blue_gam_jeom"] = 0
                update_data["red_gam_jeom"] = 0

                self.on_fight_stop.emit()

        elif command == "mch":
            update_data["match_id"] = parts[1]
            update_data["title"] = parts[2]
            update_data["category"] = parts[3]
            update_data["hit_level"] = parts[14]

            update_data["blue_points_1"] = 0
            update_data["red_points_1"] = 0
            update_data["blue_points_2"] = 0
            update_data["red_points_2"] = 0
            update_data["blue_points_3"] = 0
            update_data["red_points_3"] = 0
            update_data["blue_gam_jeom"] = 0
            update_data["red_gam_jeom"] = 0

        elif command == "rnd":
            # rnd;2
            update_data["round"] = int(parts[1])

        elif command == "at1":
            update_data["blue_name"] = parts[1]
            update_data["blue_flag"] = alpha3_to_alpha2.get(parts[3]).lower()
            update_data["red_name"] = parts[5]
            update_data["red_flag"] = alpha3_to_alpha2.get(parts[7]).lower()

            self.go_to_main_scene()

            self.socketio.emit("udp_message", {
                "event": "FightersInit",
                "blue_name": update_data["blue_name"],
                "red_name": update_data["red_name"],
                "blue_flag": update_data["blue_flag"],
                "red_flag": update_data["red_flag"],
            })

        elif command == "sc1":
            print(update_data["round"], parts[1], parts[3])
            if (update_data["round"] == 1):
                update_data["blue_points_1"] = parts[1]
                update_data["red_points_1"] = parts[3]

            elif (update_data["round"] == 2):
                update_data["blue_points_2"] = parts[1]
                update_data["red_points_2"] = parts[3]

            elif (update_data["round"] == 3):
                update_data["blue_points_3"] = parts[1]
                update_data["red_points_3"] = parts[3]

        elif command == "wg1":
            update_data["blue_gam_jeom"] = parts[1]
            update_data["red_gam_jeom"] = parts[3]

        elif command == "win":
            # brk;[break_time]
            # return {
            #     "event": "WinnerColor",
            #     "color": parts[1],
            # }

            if round_state:
                self.socketio.emit("udp_message", {
                    "event": "RoundEnd",
                    "round": update_data["round"],
                    "blue_points_1": update_data["blue_points_1"],
                    "blue_points_2": update_data["blue_points_2"],
                    "blue_points_3": update_data["blue_points_3"],
                    "red_points_1": update_data["red_points_1"],
                    "red_points_2": update_data["red_points_2"],
                    "red_points_3": update_data["red_points_3"],
                })
                round_state = False
                update_data["blue_gam_jeom"] = 0
                update_data["red_gam_jeom"] = 0

                self.on_fight_stop.emit()

        # elif command.startswith("hl"):
        #     # hl1;50 or hl2;35
        #     color = "blue" if command == "hl1" else "red"
        #     return {
        #         "event": "HitLevel",
        #         "color": color,
        #         "strength": int(parts[1]) if len(parts) > 1 else 0
        #     }
        # elif command == "wmh":
        #     # brk;[break_time]
        #     return {
        #         "event": "WinnerData",
        #         "name": parts[1],
        #         "data": parts[2],
        #     }

        #One time events
        elif command == "pt1" and parts[1] == "1":
            # brk;[break_time]
            self.socketio.emit("udp_message", {
                "event": "Punch",
                "color": "blue"
            })
        elif command == "pt2" and parts[1] == "1":
            # brk;[break_time]
            self.socketio.emit("udp_message", {
                "event": "Punch",
                "color": "red"
            })
        elif command == "pt1" and parts[1] in ["2", "4"]:
            # brk;[break_time]
            self.socketio.emit("udp_message", {
                "event": "Trunk",
                "color": "blue"
            })
        elif command == "pt2" and parts[1] in ["2", "4"]:
            # brk;[break_time]
            self.socketio.emit("udp_message", {
                "event": "Trunk",
                "color": "red"
            })
        elif command == "pt1" and parts[1] in ["3", "5"]:
            # brk;[break_time]
            self.socketio.emit("udp_message", {
                "event": "Head",
                "color": "blue"
            })
        elif command == "pt2" and parts[1] in ["3", "5"]:
            # brk;[break_time]
            self.socketio.emit("udp_message", {
                "event": "Head",
                "color": "red"
            })
        # elif command == "hel":
        #     return {
        #         "event": "Hello"
        #     }
        # elif command == "bye":
        #     return {
        #         "event": "Bye"
        #     }
        # elif command in ["inlb", "insl", "inth", "pre", "s11", "sc11", "ref", "rdy"]:
        #     return None
        # else:
        #     print(f"[Parser] Unknown command: {command}")
        #     return None

# Helper function from your original code
def get_sec(time_str):
    """Get seconds from time."""
    m, s = time_str.split(':')
    return int(m) * 60 + int(s)

def cleanup():
    """This will not be needed anymore as the worker handles cleanup."""
    pass