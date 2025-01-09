# app/cam.py
class Cam:
    def __init__(self, fps=30, resolution=(1920, 1080), device="/dev/video0", format="RGB"):
        self.fps = fps
        self.resolution = resolution
        self.device = device
        self.format = format

    def update_settings(self, fps=None, resolution=None, device=None, format=None):
        """Update camera settings."""
        if fps:
            self.fps = fps
        if resolution:
            self.resolution = resolution
        if device:
            self.device = device
        if format:
            self.format = format

    def get_source(self, idx) -> str:
        return f"shmsrc socket-path=/tmp/camera{idx}_shm_socket do-timestamp=true is-live=true"
        #return self.device

    def __repr__(self) -> str:
        return f"""
{self.device}"""