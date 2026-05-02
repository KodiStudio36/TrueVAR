# app/automation_manager.py
import asyncio
from app.automation.base_automation import BaseAutomation

class DummyAutomation(BaseAutomation):

    def __init__(self):
        super().__init__()

        self.hub.start_livestream_signal.connect(self.pre_tournament_flow)
        self.hub.start_tournament_signal.connect(self.tournament_flow)

        self.hub.on_troubleshoot_signal.connect(self.troubleshooting_flow())

    async def _pre_tournament_flow(self):
        print("Starting pre tournament flow")
        self.obs.set_starting_scene()

        self.obs.set_stinger_transition()

    async def _tournament_flow(self):
        print("Starting pre pre fight flow")
        self.obs.set_main_scene()

    async def _troubleshooting_flow(self):
        print("Starting troubleshooting flow")
        self.obs.set_troubleshooting_scene()

    # --------------------------------------------------------------------------------------------------- #

    def pre_tournament_flow(self):
        self.start_killable_flow(self._pre_tournament_flow())

    def tournament_flow(self):
        self.start_killable_flow(self._tournament_flow())
    
    def troubleshooting_flow(self):
        self.start_nuke_flow(self._troubleshooting_flow())