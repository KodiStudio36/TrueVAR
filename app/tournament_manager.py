from PyQt5.QtCore import QObject, QThread
from app.asset_worker import AssetWorker
from app.injector import singleton, Injector
from app.main_manager import MainManager

@singleton
class TournamentManager(QObject):
    def __init__(self):
        super().__init__()
        self.hub = Injector.find(MainManager)
        
        # State Storage
        self.tournament_id = None
        self.name = ""
        self.location = ""
        self.start_date = ""
        self.courts = 0
        self.stream_key = ""
        
        # Threading
        self._thread = None
        self._worker = None

        # Connect to the hub
        self.hub.on_tournament_data_signal.connect(self.update_data)

    def update_data(self, data: dict):
        """
        Expects: {'id': 3, 'name': 'myska', 'startDate': '2026-02-24', 
                 'startTime': '03:33:00', 'location': 'vf', 'courts': 2}
        """
        print(f"[Tournament] Received new data for: {data.get('name')}")
        
        # 1. Update Internal State
        self.tournament_id = data.get('id')
        self.name = data.get('name')
        self.location = data.get('location')
        self.start_date = data.get('startDate')
        self.courts = data.get('courts', 1)
        self.stream_key = data.get('stream_key', None)
        
        # 2. Logic: Should we generate assets?
        # Check if 'stream' is in data or if global streaming is enabled
        if self.stream_key: # Defaulting to True for now
            self._start_asset_generation(data)

    def _start_asset_generation(self, data):
        # 1. Is the Python reference actually holding anything?
        if self._thread is not None:
            # 2. Is the underlying C++ object still alive?
            if sip.isdeleted(self._thread):
                print("[Tournament] Thread was deleted by C++ - cleaning reference")
                self._thread = None 
            else:
                # 3. Only now is it safe to call methods on it
                try:
                    if self._thread.isRunning():
                        self._thread.quit()
                        self._thread.wait()
                except RuntimeError:
                    # Last ditch effort if it died between the check and the call
                    self._thread = None

        self._thread = QThread()
        self._worker = AssetWorker(data)
        self._worker.moveToThread(self._thread)

        # Signals
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_assets_ready)
        self._worker.error.connect(lambda err: print(f"Asset Error: {err}"))
        
        # Cleanup
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.finished.connect(lambda: setattr(self, '_thread', None))
        self._thread.start()

    def _on_assets_ready(self):
        print("[Tournament] Assets generated and ready for OBS.")
        self.hub.start_obs_signal.emit(self.stream_key)

    def get_summary(self):
        """Helper for UI components."""
        return f"{self.name} at {self.location} ({self.courts} Courts)"