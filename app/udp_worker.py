# app/udp_worker.py
from multiprocessing.pool import INIT
import socket
from traceback import print_tb
from PyQt5.QtCore import QObject, pyqtSignal
from app.injector import Injector
from app.main_manager import MainManager
from config import alpha3_to_alpha2 

INIT_STATE = "init"
READY_STATE = "ready"
FIGHT_STATE = "fight"
BREAK_STATE = "brk"
KYE_SHI_STATE = "kye_shi"

class UdpWorker(QObject):
    """
    Listens for and parses UDP packets from Tk-Strike in a dedicated thread.
    This now contains the full, correct parsing logic.
    """

    def __init__(self, port):
        super().__init__()
        self.port = port
        self._is_running = False
        self.udp_socket = None

        self.complete_data = 0

        self.hub: MainManager = Injector.find(MainManager)

        # --- State variables moved from global scope into this class ---
        self.clk_default = "02:00"
        self.reset_data()

        self.flags = {
            "mch": self.on_match,
            "at1": self.on_athletes,
            "rnd": self.on_round,
            "rdy": self.on_ready,
            "hwt": self.on_test,
            "clk": self.on_clock,
            "sc1": self.on_scoreboard,
            "wg1": self.on_penalty,
            "hl1": self.on_blue_hit,
            "hl2": self.on_red_hit,
            "brk": self.on_break,
            "win": self.on_win,
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
                    self.hub.listener_log.emit(f"[{addr[0]}] {message}")
                    print(f"[UDP] Received: {message} from {addr}")
                    # Parse the message, which updates internal state
                    self._parse_udp_message(message)


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

        self.flags.get(command, self.on_invalid)(parts)
        return

        if command == "clk":
            self.data["clk"] = parts[1][1:]
            self.clk_default = parts[1][1:]
            self.data["kye_shi"] = False
            self.data["brk"] = False

            if len(parts) > 2 and parts[2] == "start":
                self.hub.start_round_signal.emit()

        elif command == "ij0":
            self.data["clk"] = parts[1][1:]
            self.data["kye_shi"] = True
            self.data["brk"] = False
            if len(parts) > 2 and parts[2] == "hide":
                self.data["clk"] = self.clk_default
                self.data["kye_shi"] = False

        elif command == "brk":
            self.data["clk"] = parts[1][1:]
            self.data["kye_shi"] = False
            self.data["brk"] = True
            if self.round_state:
                round_end_data = {
                    "event": "RoundEnd", "round": self.data["round"],
                    "blue_name": self.data["blue_name"], "blue_flag": self.data["blue_flag"],
                    "red_name": self.data["red_name"], "red_flag": self.data["red_flag"],
                    "blue_points_1": self.data["blue_points_1"], "blue_points_2": self.data["blue_points_2"],
                    "blue_points_3": self.data["blue_points_3"], "red_points_1": self.data["red_points_1"],
                    "red_points_2": self.data["red_points_2"], "red_points_3": self.data["red_points_3"],
                }
                # self.message_parsed.emit(round_end_data)
                self.round_state = False
                self.data["blue_gam_jeom"] = 0
                self.data["red_gam_jeom"] = 0
                # self.start_break_signal.emit()

        elif command == "mch":
            self.data.update({
                "match_id": parts[1], "title": parts[2], "category": parts[3],
                "hit_level": parts[14], "blue_points_1": 0, "red_points_1": 0,
                "blue_points_2": 0, "red_points_2": 0, "blue_points_3": 0,
                "red_points_3": 0, "blue_gam_jeom": 0, "red_gam_jeom": 0
            })

            # Importnat!!! New code
            # self.hub.udp_fight_data_signal.emit({
            #     "id": parts[1], 
            #     "title": parts[2], 
            #     "category": parts[3],
            #     "hit_level": parts[14]
            # })

        elif command == "rnd":
            self.data["round"] = int(parts[1])

        elif command == "at1":
            self.data["blue_name"] = parts[1]
            self.data["blue_flag"] = alpha3_to_alpha2.get(parts[3], "UN").lower()
            self.data["red_name"] = parts[5]
            self.data["red_flag"] = alpha3_to_alpha2.get(parts[7], "UN").lower()
            fighters_init_data = {
                "event": "FightersInit",
                "blue_name": self.data["blue_name"], "red_name": self.data["red_name"],
                "blue_flag": self.data["blue_flag"], "red_flag": self.data["red_flag"],
            }
            # self.message_parsed.emit(fighters_init_data)

            # Importnat!!! New code
            # self.hub.udp_athletes_data_signal.emit({
            #     "blue_name": parts[1], 
            #     "blue_flag": alpha3_to_alpha2.get(parts[3], "UN").lower(), 
            #     "red_name": parts[5],
            #     "red_flag": alpha3_to_alpha2.get(parts[7], "UN").lower()
            # })

        elif command == "sc1":
            round_num = self.data["round"]
            if round_num == 1:
                self.data["blue_points_1"] = parts[1]
                self.data["red_points_1"] = parts[3]
            elif round_num == 2:
                self.data["blue_points_2"] = parts[1]
                self.data["red_points_2"] = parts[3]
            elif round_num == 3:
                self.data["blue_points_3"] = parts[1]
                self.data["red_points_3"] = parts[3]

        elif command == "wg1":
            self.data["blue_gam_jeom"] = parts[1]
            self.data["red_gam_jeom"] = parts[3]

        elif command == "win":
            # self.message_parsed.emit({"event": "WinnerColor", "color": parts[1]})
            # Re-using logic from 'brk' for ending the round
            self.round_state = False
            self.data["blue_gam_jeom"] = 0
            self.data["red_gam_jeom"] = 0
            # self.start_win_signal.emit()
            self.hub.start_win_signal.emit()
            self.hub.stop_recording_signal.emit()
        
        # --- One-time hit events ---
        elif command == "pt1": # Blue
            if parts[1] == "1": event_name = "Punch"
            elif parts[1] in ["2", "4"]: event_name = "Trunk"
            elif parts[1] in ["3", "5"]: event_name = "Head"
            else: return
            # self.message_parsed.emit({"event": event_name, "color": "blue"})

        elif command == "pt2": # Red
            if parts[1] == "1": event_name = "Punch"
            elif parts[1] in ["2", "4"]: event_name = "Trunk"
            elif parts[1] in ["3", "5"]: event_name = "Head"
            else: return
            # self.message_parsed.emit({"event": event_name, "color": "red"})

    def on_match(self, parts):
        if self.complete_data == 0: self.reset_data()

        self.data.update({
                "id": parts[1], 
                "title": parts[2], 
                "category": parts[3],
                "hit_level": parts[14],
            })
    
        self.emit_stable_update()
        self.emit_new_fight()

    def on_athletes(self, parts):
        if self.complete_data == 0: self.reset_data()

        self.data.update({
                "blue_name": parts[1], 
                "blue_flag2": alpha3_to_alpha2.get(parts[3], "UN").lower(), 
                "blue_flag3": parts[3], 
                "red_name": parts[5],
                "red_flag2": alpha3_to_alpha2.get(parts[7], "UN").lower(),
                "red_flag3": parts[7],
            })
        
        self.emit_stable_update()
        self.emit_new_fight()

    def on_round(self, parts):
        self.data["round"] = int(parts[1])

        self.emit_stable_update()

    def on_ready(self, parts):
        self.data["state"] = READY_STATE

    def on_test(self, parts):
        if self.data["state"] == READY_STATE:
            self.emit_start_fight()

    def on_clock(self, parts):
        self.data["clk"] = parts[1][1:]
        self.clk_default = parts[1][1:]

        if self.data["state"] not in [FIGHT_STATE, INIT_STATE]:
            self.data["state"] = FIGHT_STATE
            self.emit_start_fight()

            self.emit_start_round()
        
        self.emit_fast_clk_update()

    def on_scoreboard(self, parts):
        self.data["blue_points"][self.data["round"] - 1]["points"] = parts[1]
        self.data["red_points"][self.data["round"] - 1]["points"] = parts[3]

    def on_penalty(self, parts):
        self.data["blue_points"][self.data["round"] - 1]["penalties"] = parts[1]
        self.data["red_points"][self.data["round"] - 1]["penalties"] = parts[3]
    
    def on_blue_hit(self, parts):
        self.data["blue_points"][self.data["round"] - 1]["hits"] += 1
    
    def on_red_hit(self, parts):
        self.data["red_points"][self.data["round"] - 1]["hits"] += 1

    def on_break(self, parts):
        self.data["clk"] = parts[1][1:]
        if self.data["state"] == FIGHT_STATE:
            self.data["state"] = BREAK_STATE
            self.emit_stable_update()
            self.emit_start_break()

        self.emit_fast_clk_update()

    def on_win(self, parts):
        self.data["win"] = parts[1].lower()
        self.emit_stable_update()
        self.emit_win()

    def on_invalid(self, parts):
        pass
        
    def emit_stable_update(self):
        self.hub.listener_stable_signal.emit({"event": "update", "data": self.data})

    def emit_fast_clk_update(self):
        self.hub.listener_fast_signal.emit({"event": "clock", "data": {"clk": self.data["clk"]}})
    
    def emit_new_fight(self):
        self.complete_data += 1
        
        if self.complete_data == 2:
            self.hub.new_fight_signal.emit()
            self.complete_data = 0

    def emit_start_fight(self):
        if not self.data["fight_started"]:
            self.data["fight_started"] = True
            self.hub.start_fight_signal.emit()

    def emit_start_round(self):
        self.hub.start_round_signal.emit()

    def emit_start_break(self):
        self.hub.start_break_signal.emit()

    def emit_win(self):
        self.hub.win_signal.emit()
        self.hub.stop_recording_signal.emit()
        self.data["state"] = INIT_STATE
    
    def reset_data(self):
        self.data = {
            "clk": "", 
            "state": INIT_STATE,
            "id": 0,
            "title": "", 
            "category": "", 
            "hit_level": 0, 
            "round": 1, 
            "win": "",
            "fight_started": False,
            "blue_name": "",
            "blue_flag2": "", 
            "blue_flag3": "", 
            "blue_points": [{
                "points": 0,
                "hits": 0,
                "trunk": 0,
                "rotation_trunk": 0,
                "head": 0,
                "rotation_head": 0,
                "punch": 0,
                "penalties": 0,
            }, 
            {
                "points": 0,
                "hits": 0,
                "trunk": 0,
                "rotation_trunk": 0,
                "head": 0,
                "rotation_head": 0,
                "punch": 0,
                "penalties": 0,
            },
            {
                "points": 0,
                "hits": 0,
                "trunk": 0,
                "rotation_trunk": 0,
                "head": 0,
                "rotation_head": 0,
                "punch": 0,
                "penalties": 0,
            }],
            "red_name": "", 
            "red_flag2": "", 
            "red_flag3": "", 
            "red_points": [{
                "points": 0,
                "hits": 0,
                "trunk": 0,
                "rotation_trunk": 0,
                "head": 0,
                "rotation_head": 0,
                "punch": 0,
                "penalties": 0,
            }, 
            {
                "points": 0,
                "hits": 0,
                "trunk": 0,
                "rotation_trunk": 0,
                "head": 0,
                "rotation_head": 0,
                "punch": 0,
                "penalties": 0,
            },
            {
                "points": 0,
                "hits": 0,
                "trunk": 0,
                "rotation_trunk": 0,
                "head": 0,
                "rotation_head": 0,
                "punch": 0,
                "penalties": 0,
            }],
        }