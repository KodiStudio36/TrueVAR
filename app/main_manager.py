from PyQt5.QtCore import QObject, pyqtSignal
from app.injector import singleton

@singleton
class MainManager(QObject):
    # --- In App Navigation ---
    show_settings_signal = pyqtSignal()
    hide_settings_signal = pyqtSignal()
    show_replay_signal = pyqtSignal() # Used for ivr automation
    hide_replay_signal = pyqtSignal()

    toggle_recording_signal = pyqtSignal()
    start_recording_signal = pyqtSignal()
    stop_recording_signal = pyqtSignal()

    # --- Server Stream Controls ---
    on_tournament_data_signal = pyqtSignal(dict)
    start_obs_signal = pyqtSignal()
    start_livestream_signal = pyqtSignal()
    stop_livestream_signal = pyqtSignal()
    start_tournament_signal = pyqtSignal()
    stop_tournament_signal = pyqtSignal()

    other_fight_started_signal = pyqtSignal()

    # --- Udp Signals ---
    udp_fight_data_signal = pyqtSignal(dict)
    udp_athletes_data_signal = pyqtSignal(dict)
    udp_update_fight_data_signal = pyqtSignal()
    udp_update_clock_signal = pyqtSignal()

    udp_start_round_signal = pyqtSignal()
    # udp_start_break_signal = pyqtSignal()
    # udp_start_win_signal = pyqtSignal()

    udp_punch_signal = pyqtSignal()
    udp_trunk_signal = pyqtSignal()
    udp_head_signal = pyqtSignal()

    # --- Fight Manager Signals ---
    new_fight_signal = pyqtSignal()
    update_fight_data_signal = pyqtSignal()
    start_fight_signal = pyqtSignal()

    def __init__(self):
        super().__init__()