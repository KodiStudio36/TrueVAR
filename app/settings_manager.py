import json
import os

class SettingsManager:
    """Base class for all settings managers."""
    _auto_save = True  # Save automatically when a field changes

    def __init__(self, filepath):
        self.filepath = filepath
        self.load()

    def save(self):
        data = {name: getattr(self, name) for name in getattr(self, "_settings_fields", [])}
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=4)

    def load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                data = json.load(f)
                for name in getattr(self, "_settings_fields", []):
                    if name in data:
                        setattr(self, name, data[name])
        else:
            self.save()  # create default file

class Setting:
    """Descriptor to mark attributes as persisted settings."""
    def __init__(self, default=None):
        self.default = default
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name
        if not hasattr(owner, "_settings_fields"):
            owner._settings_fields = []
        owner._settings_fields.append(name)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name, self.default)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value
        if hasattr(instance, "_auto_save") and instance._auto_save:
            instance.save()
