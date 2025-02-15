# app/cam.py
class Cam:
    def __init__(self, device="/dev/video0"):
        self.device = device

    def update_settings(self, device=None):
        """Update camera settings."""
        if device:
            self.device = device

    def get_source(self, idx) -> str:
        return f"shmsrc socket-path=/tmp/camera{idx}_shm_socket do-timestamp=true is-live=true"
        #return self.device

    def __repr__(self) -> str:
        return f"""
{self.device}"""