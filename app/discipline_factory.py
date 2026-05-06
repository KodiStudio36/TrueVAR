# app/factory/discipline_factory.py
from app.listeners.kyorugi_daedo_listener import KyorugiDaedoListener
from app.listeners.dummy_listener import DummyListener

from app.automation.kyorugi_automation import KyorugiAutomation
from app.automation.dummy_automation import DummyAutomation

class DisciplineFactory:

    @staticmethod
    def create(discipline: str):
        discipline = discipline.lower()

        if discipline == "kyorugi daedo":
            return KyorugiDaedoListener(), KyorugiAutomation()

        elif discipline == "poomsae fitofan":
            return DummyListener(), DummyAutomation()

        else:
            raise ValueError(f"Unknown discipline: {discipline}")