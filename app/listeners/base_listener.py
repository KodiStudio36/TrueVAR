from PyQt5.QtCore import QObject

class BaseListener(QObject):
    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError