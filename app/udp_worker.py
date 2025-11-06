# app/udp_worker.py
import socket
from PyQt5.QtCore import QObject, pyqtSignal

# This should be imported from your config file
from config import alpha3_to_alpha2 

class UdpWorker(QObject):
    """
    Listens for and parses UDP packets from Tk-Strike in a dedicated thread.
    This now contains the full, correct parsing logic.
    """
    # This signal will emit dictionaries for broadcasting via Socket.IO
    message_parsed = pyqtSignal(dict)
    
    # These signals are for high-level application events (like recording)
    fight_started = pyqtSignal()
    fight_stopped = pyqtSignal()

    def __init__(self, port):
        super().__init__()
        self.port = port
        self._is_running = False
        self.udp_socket = None

        # --- State variables moved from global scope into this class ---
        self.round_state = False
        self.stream_started = False
        self.clk = "02:00" # Default clock
        self.update_data = {
            "event": "Update", "clk": "", "kye_shi": False, "brk": False, "match_id": 0,
            "title": "", "category": "", "hit_level": 0, "round": 1, "blue_name": "",
            "blue_flag": "", "blue_points_1": 0, "blue_points_2": 0, "blue_points_3": 0,
            "blue_gam_jeom": 0, "red_name": "", "red_flag": "", "red_points_1": 0,
            "red_points_2": 0, "red_points_3": 0, "red_gam_jeom": 0,
        }

    def start_listener(self):
        self._is_running = True
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.udp_socket.bind(("0.0.0.0", self.port))
            print(f"[UDP Worker] Listening on 0.0.0.0:{self.port}...")
        except OSError as e:
            print(f"[UDP Worker] FATAL: Could not bind to port {self.port}. {e}")
            self._is_running = False
            return

        while self._is_running:
            try:
                self.udp_socket.settimeout(1.0)
                data, addr = self.udp_socket.recvfrom(2048)
                message = data.decode(errors='ignore').strip()
                if message:
                    print(f"[UDP] Received: {message} from {addr}")
                    # Parse the message, which updates internal state
                    self._parse_udp_message(message)
                    # After parsing, always emit the main update_data dictionary
                    self.message_parsed.emit(self.update_data.copy())
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[UDP Worker] Error: {e}")
        
        if self.udp_socket:
            self.udp_socket.close()
        print("[UDP Worker] Listener has stopped.")

    def stop_listener(self):
        print("[UDP Worker] Stopping listener...")
        self._is_running = False

    def _parse_udp_message(self, msg: str):
        parts = msg.strip().split(";")
        if not parts:
            return

        command = parts[0].lower()

        if command == "clk":
            self.update_data["clk"] = parts[1][1:]
            self.clk = parts[1][1:]
            self.update_data["kye_shi"] = False
            self.update_data["brk"] = False

            if len(parts) > 2 and parts[2] == "start" and not self.round_state:
                self.message_parsed.emit({"event": "RoundStart"})
                self.round_state = True
                self.fight_started.emit() # Emit signal for application logic
                if not self.stream_started:
                    self.stream_started = True # Note: this worker can't change OBS scenes
                                               # The main app must listen to the signal.

        elif command == "ij0":
            self.update_data["clk"] = parts[1][1:]
            self.update_data["kye_shi"] = True
            self.update_data["brk"] = False
            if len(parts) > 2 and parts[2] == "hide":
                self.update_data["clk"] = self.clk
                self.update_data["kye_shi"] = False

        elif command == "brk":
            self.update_data["clk"] = parts[1][1:]
            self.update_data["kye_shi"] = False
            self.update_data["brk"] = True
            if self.round_state:
                round_end_data = {
                    "event": "RoundEnd", "round": self.update_data["round"],
                    "blue_name": self.update_data["blue_name"], "blue_flag": self.update_data["blue_flag"],
                    "red_name": self.update_data["red_name"], "red_flag": self.update_data["red_flag"],
                    "blue_points_1": self.update_data["blue_points_1"], "blue_points_2": self.update_data["blue_points_2"],
                    "blue_points_3": self.update_data["blue_points_3"], "red_points_1": self.update_data["red_points_1"],
                    "red_points_2": self.update_data["red_points_2"], "red_points_3": self.update_data["red_points_3"],
                }
                self.message_parsed.emit(round_end_data)
                self.round_state = False
                self.update_data["blue_gam_jeom"] = 0
                self.update_data["red_gam_jeom"] = 0
                self.fight_stopped.emit()

        elif command == "mch":
            self.update_data.update({
                "match_id": parts[1], "title": parts[2], "category": parts[3],
                "hit_level": parts[14], "blue_points_1": 0, "red_points_1": 0,
                "blue_points_2": 0, "red_points_2": 0, "blue_points_3": 0,
                "red_points_3": 0, "blue_gam_jeom": 0, "red_gam_jeom": 0
            })

        elif command == "rnd":
            self.update_data["round"] = int(parts[1])

        elif command == "at1":
            self.update_data["blue_name"] = parts[1]
            self.update_data["blue_flag"] = alpha3_to_alpha2.get(parts[3], "UN").lower()
            self.update_data["red_name"] = parts[5]
            self.update_data["red_flag"] = alpha3_to_alpha2.get(parts[7], "UN").lower()
            fighters_init_data = {
                "event": "FightersInit",
                "blue_name": self.update_data["blue_name"], "red_name": self.update_data["red_name"],
                "blue_flag": self.update_data["blue_flag"], "red_flag": self.update_data["red_flag"],
            }
            self.message_parsed.emit(fighters_init_data)

        elif command == "sc1":
            round_num = self.update_data["round"]
            if round_num == 1:
                self.update_data["blue_points_1"] = parts[1]
                self.update_data["red_points_1"] = parts[3]
            elif round_num == 2:
                self.update_data["blue_points_2"] = parts[1]
                self.update_data["red_points_2"] = parts[3]
            elif round_num == 3:
                self.update_data["blue_points_3"] = parts[1]
                self.update_data["red_points_3"] = parts[3]

        elif command == "wg1":
            self.update_data["blue_gam_jeom"] = parts[1]
            self.update_data["red_gam_jeom"] = parts[3]

        elif command == "win":
            self.message_parsed.emit({"event": "WinnerColor", "color": parts[1]})
            if self.round_state:
                # Re-using logic from 'brk' for ending the round
                self.round_state = False
                self.update_data["blue_gam_jeom"] = 0
                self.update_data["red_gam_jeom"] = 0
                self.fight_stopped.emit()
        
        # --- One-time hit events ---
        elif command == "pt1": # Blue
            if parts[1] == "1": event_name = "Punch"
            elif parts[1] in ["2", "4"]: event_name = "Trunk"
            elif parts[1] in ["3", "5"]: event_name = "Head"
            else: return
            self.message_parsed.emit({"event": event_name, "color": "blue"})

        elif command == "pt2": # Red
            if parts[1] == "1": event_name = "Punch"
            elif parts[1] in ["2", "4"]: event_name = "Trunk"
            elif parts[1] in ["3", "5"]: event_name = "Head"
            else: return
            self.message_parsed.emit({"event": event_name, "color": "red"})