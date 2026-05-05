# app/automation_manager.py
import asyncio
from app.automation.base_automation import BaseAutomation

class KyorugiAutomation(BaseAutomation):

    def __init__(self):
        super().__init__()

        self.hub.start_livestream_signal.connect(self.pre_tournament_flow)
        self.hub.start_tournament_signal.connect(self.pre_pre_fight_flow)
        
        self.hub.new_fight_signal.connect(self.pre_fight_flow)
        self.hub.start_fight_signal.connect(self.start_fight_flow)
        self.hub.start_round_signal.connect(self.start_round_flow)
        self.hub.start_break_signal.connect(self.post_round_flow)
        self.hub.win_signal.connect(self.post_fight_flow)

        self.hub.stream_message_broadcast_signal.connect(lambda m: self.message_broadcast_flow(m))

        self.hub.on_troubleshoot_signal.connect(self.troubleshooting_flow())
        self.hub.start_ivr_signal.connect(self.start_ivr_flow())
        self.hub.start_ivr_closeup_signal.connect(self.start_ivr_closeup_flow())
        self.hub.stop_ivr_signal.connect(self.post_ivr_flow())

    async def _pre_tournament_flow(self):
        print("Starting pre tournament flow")
        self.obs.set_starting_scene()
        self.obs.set_move_transition()

    async def _pre_pre_fight_flow(self):
        print("Starting pre pre fight flow")
        self.web.reset_widgets(["widget-winner", "widget-round-results"])

        self.obs.set_main_scene()

    async def _pre_fight_flow(self):
        print("Starting pre fight flow")
        self.web.reset_widgets(["widget-winner", "widget-round-results"])

        self.obs.set_main_scene()

        await asyncio.sleep(.5)

        self.web.show_next_round_widget()

    async def _start_fight_flow(self):
        print("Starting start fight flow")
        self.web.reset_widgets()
        
        self.web.show_fighter_bars_widget()

        await asyncio.sleep(8)

        self.web.hide_fighter_bars_widget()

    async def _start_round_flow(self):
        print("Starting start round flow")
        self.web.reset_widgets(["widget-winner", "widget-round-results"])

        self.obs.set_main_scene_w_scoreboard()

        await asyncio.sleep(.2)

        self.web.hide_next_round_widget()

    async def _post_round_flow(self):
        print("Starting post round flow")
        self.web.reset_widgets()

        self.obs.set_main_scene()

        await asyncio.sleep(4)

        self.web.show_round_results_widget()

        await asyncio.sleep(10)

        self.web.hide_round_results_widget()


    async def _post_fight_flow(self):
        print("Starting post fight flow")
        self.web.reset_widgets()

        self.obs.set_main_scene()
        await asyncio.sleep(2)
        self.web.show_win_widget()
        await asyncio.sleep(8)
        self.web.hide_win_widget()

        await self._post_round_flow()

    async def _start_ivr_flow(self):
        print("Starting start ivr flow")
        self.obs.set_stinger_transition()

        await asyncio.sleep(2) # This a is constant
        self.web.show_ivr_widget()

        await asyncio.sleep(5)
        self.web.hide_ivr_widget()
        self.obs.set_ivr_scene()

        await asyncio.sleep(3)
        self.obs.set_stinger_transition()

    async def _start_ivr_closeup_flow(self):
        print("Starting start ivr closeup flow")
        self.obs.set_move_transition()
        self.obs.set_ivr_closeup_scene()

        await asyncio.sleep(3)
        self.obs.set_stinger_transition()

    async def _post_ivr_flow(self):
        print("Starting post ivr flow")
        self.web.reset_widgets(["widget-ivr"])
        self.obs.set_main_scene_w_scoreboard()

        await asyncio.sleep(3)
        self.obs.set_move_transition()

    async def _message_broadcast_flow(self, data):
        print("Starting message broadcast flow")

        self.web.show_ticker_widget(data)

    async def _troubleshooting_flow(self):
        print("Starting troubleshooting flow")
        self.web.reset_widgets()

        self.obs.set_stinger_transition()
        await asyncio.sleep(.5)

        self.obs.set_troubleshooting_scene()

    # --------------------------------------------------------------------------------------------------- #

    def pre_tournament_flow(self):
        self.start_killable_flow(self._pre_tournament_flow())

    def pre_fight_flow(self):
        self.start_killable_flow(self._pre_fight_flow())

    def pre_pre_fight_flow(self):
        self.start_killable_flow(self._pre_pre_fight_flow())

    def start_fight_flow(self):
        self.start_async_flow(self._start_fight_flow())

    def start_round_flow(self):
        self.start_killable_flow(self._start_round_flow())

    def post_round_flow(self):
        self.start_killable_flow(self._post_round_flow())

    def post_fight_flow(self):
        self.start_killable_flow(self._post_fight_flow())

    def start_ivr_flow(self):
        self.start_killable_flow(self._start_ivr_flow())

    def start_ivr_closeup_flow(self):
        self.start_killable_flow(self._start_ivr_closeup_flow())

    def post_ivr_flow(self):
        self.start_killable_flow(self._post_ivr_flow())

    def message_broadcast_flow(self, data):
        self.start_async_flow(self._message_broadcast_flow(data))
    
    def troubleshooting_flow(self):
        self.start_nuke_flow(self._troubleshooting_flow())