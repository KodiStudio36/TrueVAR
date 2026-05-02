# app/automation_manager.py
import asyncio
from PyQt5.QtCore import QObject
from app.injector import Injector
from app.obs_manager import OBSManager
from app.webserver_manager import WebServerManager
from app.main_manager import MainManager


class BaseAutomation(QObject):

    def __init__(self):
        super().__init__()

        self.obs: OBSManager = Injector.find(OBSManager)
        self.web: WebServerManager = Injector.find(WebServerManager)
        self.hub: MainManager = Injector.find(MainManager)

        self.current_task: asyncio.Task | None = None
        self.async_tasks: set[asyncio.Task] = set()

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