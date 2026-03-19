# app/automation_manager.py
import asyncio
from PyQt5.QtCore import QObject
from app.injector import singleton, Injector
from app.obs_manager import OBSManager
from app.webserver_manager import WebServerManager
from app.main_manager import MainManager


@singleton
class AutomationManager(QObject):

    def __init__(self):
        super().__init__()

        self.obs: OBSManager = Injector.find(OBSManager)
        self.web: WebServerManager = Injector.find(WebServerManager)
        self.hub: MainManager = Injector.find(MainManager)
        # self.udp: UdpManager = Injector.find(UdpManager)

        self.current_task: asyncio.Task | None = None
        self.current_priority = 0

        # # Subscribe to UDP events
        # self.udp.message_parsed.connect(self.handle_udp_event)

        self.hub.start_livestream_signal.connect(self.pre_tournament_flow)
        self.hub.start_tournament_signal.connect(self.pre_fight_flow)

    # ------------------------
    # FLOWS
    # ------------------------

    async def _pre_tournament_flow(self):
        print("Starting pre tournament flow")

        self.obs.set_starting_scene()

    async def _pre_fight_flow(self):
        print("Starting pre fight flow")

        self.obs.set_main_scene()

    async def _start_fight_flow(self):
        print("Starting start fight flow")

        await self._start_round_flow()

    async def _start_round_flow(self):
        print("Starting start round flow")

        self.obs.set_main_scene_w_scoreboard()

    async def _post_round_flow(self):
        print("Starting post round flow")

        self.obs.set_main_scene()

    async def _post_fight_flow(self):
        print("Starting post fight flow")

        self.obs.set_main_scene()

        await self._post_round_flow()

    async def _start_ivr_flow(self):
        print("Starting start ivr flow")
        self.web.show_ivr_widget()
        await asyncio.sleep(5)
        self.web.hide_ivr_widget()
        self.obs.set_ivr_scene()

    async def _start_ivr_closeup_flow(self):
        print("Starting start ivr closeup flow")

        self.obs.set_ivr_closeup_scene()

    async def _post_ivr_flow(self):
        print("Starting post ivr flow")

        self.obs.set_main_scene_w_scoreboard()

    async def _troubleshooting_flow(self):
        print("Starting troubleshooting flow")

        self.obs.set_troubleshooting_scene()


    # ------------------------
    # CONTROL
    # ------------------------

    def start_flow(self, coro, priority=1):
        # If new flow has higher priority → interrupt
        if self.current_task:
            if priority < self.current_priority:
                return  # ignore lower priority
            self.current_task.cancel()

        self.current_priority = priority

        loop = asyncio.get_running_loop()
        self.current_task = loop.create_task(self._run_flow(coro))

    async def _run_flow(self, coro):
        try:
            await coro
        except asyncio.CancelledError:
            print("Flow cancelled")
        finally:
            self.current_priority = 0
            self.current_task = None

    # ------------------------
    # PUBLIC AUTOMATIONS
    # ------------------------

    def pre_tournament_flow(self):
        self.start_flow(self._pre_tournament_flow(), priority=1)

    def pre_fight_flow(self):
        self.start_flow(self._pre_fight_flow(), priority=1)

    def start_fight_flow(self):
        self.start_flow(self._start_fight_flow(), priority=1)

    def start_round_flow(self):
        self.start_flow(self._start_round_flow(), priority=1)

    def post_round_flow(self):
        self.start_flow(self._post_round_flow(), priority=1)

    def post_fight_flow(self):
        self.start_flow(self._post_fight_flow(), priority=1)

    def start_ivr_flow(self):
        self.start_flow(self._start_ivr_flow(), priority=1)

    def start_ivr_closeup_flow(self):
        self.start_flow(self._start_ivr_closeup_flow(), priority=1)

    def post_ivr_flow(self):
        self.start_flow(self._post_ivr_flow(), priority=1)
    
    def troubleshooting_flow(self):
        self.start_flow(self._troubleshooting_flow(), priority=1)

    # ------------------------
    # UDP EVENT HANDLER
    # ------------------------

    def handle_udp_event(self, data: dict):
        event = data.get("event")

        if event == "RoundStart":
            self.start_round_flow()

        elif event == "RoundEnd":
            self.post_round_flow()

        elif event == "WinnerColor":
            self.post_fight_flow()