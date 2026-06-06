# app/factory/discipline_factory.py
from app.automation.poomsae_automation import PoomsaeAutomation
from app.listeners.kyorugi_daedo_listener import KyorugiDaedoListener
from app.listeners.dummy_listener import DummyListener

from app.automation.kyorugi_automation import KyorugiAutomation
from app.automation.dummy_automation import DummyAutomation
from app.listeners.poomsae_fitofan_listener import PoomsaeFitofanListener

class DisciplineFactory:

    @staticmethod
    def create(discipline: str):
        discipline = discipline.lower()

        if discipline == "kyorugi daedo":
            return KyorugiDaedoListener(), KyorugiAutomation()

        elif discipline == "poomsae fitofan":
            return PoomsaeFitofanListener(), PoomsaeAutomation()

        else:
            raise ValueError(f"Unknown discipline: {discipline}")