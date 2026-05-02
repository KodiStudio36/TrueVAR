# app/listeners/dummy_listener.py
from app.listeners.base_listener import BaseListener

class DummyListener(BaseListener):
    def start(self):
        print("[Listener] Dummy listener started (no-op)")

    def stop(self):
        print("[Listener] Dummy listener stopped")