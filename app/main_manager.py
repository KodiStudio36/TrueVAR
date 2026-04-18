from PyQt5.QtCore import QObject, pyqtSignal
from app.injector import singleton

@singleton
class MainManager(QObject):
    # --- In App Navigation ---
    show_settings_signal = pyqtSignal()
    hide_settings_signal = pyqtSignal()
    show_replay_signal = pyqtSignal()
    hide_replay_signal = pyqtSignal()

    toggle_recording_signal = pyqtSignal()
    start_recording_signal = pyqtSignal()
    stop_recording_signal = pyqtSignal()

    # --- Server Stream Controls ---
    on_tournament_data_signal = pyqtSignal(dict)
    start_obs_signal = pyqtSignal(str)
    start_livestream_signal = pyqtSignal()
    stop_livestream_signal = pyqtSignal()
    start_tournament_signal = pyqtSignal()
    stop_tournament_signal = pyqtSignal()

    other_fight_started_signal = pyqtSignal()
    stream_message_broadcast_signal = pyqtSignal(str)

    # --- Udp Signals ---
    listener_log = pyqtSignal(str)
    listener_stable_signal = pyqtSignal(dict)
    listener_fast_signal = pyqtSignal(dict)

    # --- Fight Manager Signals ---
    new_fight_signal = pyqtSignal()
    start_fight_signal = pyqtSignal()
    start_round_signal = pyqtSignal()
    start_break_signal = pyqtSignal()
    win_signal = pyqtSignal()

    def __init__(self):
        super().__init__()