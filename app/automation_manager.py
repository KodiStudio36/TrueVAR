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
        self.async_tasks: set[asyncio.Task] = set()
        # # Subscribe to UDP events
        # self.udp.message_parsed.connect(self.handle_udp_event)

        self.hub.start_livestream_signal.connect(self.pre_tournament_flow)
        self.hub.start_tournament_signal.connect(self.pre_pre_fight_flow)
        self.hub.new_fight_signal.connect(self.pre_fight_flow)
        self.hub.start_fight_signal.connect(self.start_fight_flow)
        self.hub.start_round_signal.connect(self.start_round_flow)
        self.hub.start_break_signal.connect(self.post_round_flow)
        self.hub.win_signal.connect(self.post_fight_flow)
        self.hub.stream_message_broadcast_signal.connect(lambda m: self.message_broadcast_flow(m))

    # ------------------------
    # FLOWS
    # ------------------------

    async def _pre_tournament_flow(self):
        print("Starting pre tournament flow")
        self.obs.set_starting_scene()

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

        await asyncio.sleep(2)

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


    # ------------------------
    # EXECUTION CONTROLLERS
    # ------------------------

    def start_killable_flow(self, coro):
        """Starts an exclusive flow. Kills the currently running killable flow (if any)."""
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()

        loop = asyncio.get_running_loop()
        self.current_task = loop.create_task(self._run_killable(coro))

    async def _run_killable(self, coro):
        try:
            await coro
        except asyncio.CancelledError:
            print(f"Killable flow cancelled: {coro.__name__}")
        finally:
            self.current_task = None

    def start_async_flow(self, coro):
        """Starts a fully independent background flow. Cannot be killed except by a nuke."""
        loop = asyncio.get_running_loop()
        task = loop.create_task(self._run_async(coro))
        
        self.async_tasks.add(task)
        # Automatically remove task from the set when it finishes to prevent memory leaks
        task.add_done_callback(self.async_tasks.discard)

    async def _run_async(self, coro):
        try:
            await coro
        except asyncio.CancelledError:
            print(f"Async flow cancelled (Nuked): {coro.__name__}")

    def start_nuke_flow(self, coro):
        """Kills EVERYTHING (current killable + all async flows), then runs."""
        # 1. Kill standard killable task
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
        
        # 2. Kill all background async tasks
        for task in self.async_tasks:
            if not task.done():
                task.cancel()
        
        # 3. Start the new flow as the main killable task
        loop = asyncio.get_running_loop()
        self.current_task = loop.create_task(self._run_killable(coro))

    # ------------------------
    # PUBLIC AUTOMATIONS
    # ------------------------

    # Standard exclusive flows (kill other killables)
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