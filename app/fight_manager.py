from PyQt5.QtCore import QObject, pyqtSignal
from app.injector import singleton, Injector
from app.main_manager import MainManager

FIGHT_STATE = "fight"
BREAK_STATE = "brk"
KYE_SHI_STATE = "kye_shi"

@singleton
class FightManager(QObject):

    def __init__(self):
        super().__init__()
        self.hub = Injector.find(MainManager)

        self.complete_data = 0
        
        self.reset_fight()

        self.hub.udp_fight_data_signal.connect(self.set_fight_data)
        self.hub.udp_athletes_data_signal.connect(self.set_athletes_data)
        self.hub.udp_start_round_signal.connect(self.start_round)

    def emit_new_fight(self):
        self.complete_data += 1
        
        if self.complete_data == 2:
            self.hub.new_fight_signal.emit()
            self.complete_data = 0

    def emit_start_fight(self):
        if not self.fight_started:
            self.hub.start_fight_signal.emit()
            self.fight_started = True

    def set_fight_data(self, data):
        self.reset_fight()

        self.id = data["id"]
        self.title = data["title"]
        self.category = data["category"]
        self.hit_level = data["hit_level"]

        self.emit_new_fight()

    def set_athletes_data(self, data):
        self.blue_name = data["blue_name"]
        self.blue_flag = data["blue_flag"]
        self.red_name = data["red_name"]
        self.red_flag = data["red_flag"]

        self.emit_new_fight()

    def start_round(self):
        self.emit_start_fight()

    def reset_fight(self):
        self.id = 0
        self.title = ""
        self.category = ""
        self.hit_level = 0
        self.state = FIGHT_STATE
        self.clock = "02:00"
        self.round = 1
        
        self.blue_points = [0, 0, 0]
        self.blue_gam_jeoms = [0, 0, 0]

        self.red_points = [0, 0, 0]
        self.red_gam_jeoms = [0, 0, 0]

        self.fight_started = False

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "hit_level": self.hit_level,
            "state": self.state,
            "clock": self.clock,
            "round": self.round,
            
            "blue_name": self.blue_name,
            "blue_flag": self.blue_flag,
            "blue_points": self.blue_points,
            "blue_gam_jeoms": self.blue_gam_jeoms,

            "red_name": self.red_name,
            "red_flag": self.red_flag,
            "red_points": self.red_points,
            "red_gam_jeoms": self.red_gam_jeoms,
        }