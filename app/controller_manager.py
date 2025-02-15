import json, os, subprocess, signal
from config import controller_settings_file

class ControllerManager:
    def __init__(self):
        self.command = None
        self.command_str = ""

        self.load_command()

    def start(self):
        if self.command_str != "":
            try:
                print("bbbb")
                self.command = subprocess.Popen(
                    [self.command_str], 
                    stdout=subprocess.DEVNULL,
                    shell=True, 
                    start_new_session=True
                )
                
            except:
                print("Errooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooor")
                pass

    def stop(self):
        if self.command != None:
            os.killpg(os.getpgid(self.command.pid), signal.SIGTERM)
            self.command = None

    def reload(self):
        self.stop()
        self.start()

    def save_command(self, command):
        data = {
            "command": command,
        }
        with open(controller_settings_file, 'w') as f:
            json.dump(data, f, indent=4)

        self.load_command()

    def load_command(self):
        """Load key binds from a JSON file."""
        if os.path.exists(controller_settings_file):
            with open(controller_settings_file, 'r') as f:
                data = json.load(f)
                self.command_str = data["command"]