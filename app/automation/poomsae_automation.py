# app/automation_manager.py
import asyncio
from app.automation.base_automation import BaseAutomation

class PoomsaeAutomation(BaseAutomation):

    def __init__(self):
        super().__init__()

        # self.hub.start_livestream_signal.connect(self.pre_tournament_flow)
        # self.hub.start_tournament_signal.connect(self.pre_pre_fight_flow)
        
        # self.hub.new_fight_signal.connect(self.pre_fight_flow)
        # self.hub.start_fight_signal.connect(self.start_fight_flow)
        self.hub.start_round_signal.connect(self.start_round_flow)
        self.hub.start_break_signal.connect(self.post_round_flow)
        # self.hub.win_signal.connect(self.post_fight_flow)

        # self.hub.stream_message_broadcast_signal.connect(lambda m: self.message_broadcast_flow(m))

        # self.hub.on_troubleshoot_signal.connect(self.troubleshooting_flow)
        # self.hub.start_ivr_signal.connect(self.start_ivr_flow)
        # self.hub.start_ivr_closeup_signal.connect(self.start_ivr_closeup_flow)
        # self.hub.stop_ivr_signal.connect(self.post_ivr_flow)

    async def _start_round_flow(self):
        print("Starting start round flow")

        self.web.hide_clock_widget()

    async def _post_round_flow(self):
        print("Starting post round flow")

        self.web.show_clock_widget()

    # --------------------------------------------------------------------------------------------------- #

    def start_round_flow(self):
        self.start_killable_flow(self._start_round_flow())

    def post_round_flow(self):
        self.start_killable_flow(self._post_round_flow())