import sys, os, asyncio
from PyQt5.QtWidgets import QApplication, QDialog
from app.tournament_manager import TournamentManager
from interface.main_window import MainWindow
from interface.dialogs.license_dialog import LicenseDialog
from interface.dialogs.tournament_dialog import TournamentSelectionDialog
from interface.dialogs.loading_dialog import StartupLoaderDialog  # <-- New Import
from app.license_manager import LicenseManager
from app.socket_manager import SocketManager
from app.injector import Injector
from config import records_path, settings_path 

from qasync import QEventLoop as AsyncioPyQtLoop 
from PyQt5.QtCore import QEventLoop as QtNativeLoop

def main():
    app = QApplication(sys.argv)

    # 1. Setup the asyncio/PyQt bridge
    event_loop = AsyncioPyQtLoop(app)
    asyncio.set_event_loop(event_loop)

    os.makedirs(records_path, exist_ok=True)
    os.makedirs(settings_path, exist_ok=True)

    license_manager = Injector.find(LicenseManager)
    socket_manager = Injector.find(SocketManager)
    tournament_manager = Injector.find(TournamentManager)

    license_manager.connection_ready.connect(socket_manager.connect)

    def handle_tournaments(tournaments_list):
        # If tournaments_list is a list of objects like [{"name": "A", "courts": 4}, ...]
        # we convert it to a dict: {"A": 4, "B": 2}
        mapping = {t['name']: int(t['courts']) for t in tournaments_list}
        
        sel_dialog = TournamentSelectionDialog(mapping)
        if sel_dialog.exec_() == QDialog.Accepted:
            choice_name, choice_court = sel_dialog.get_selection()
            socket_manager.select_tournament(choice_name, choice_court)

    def handle_final_data(_):
        wait_loop.quit() 

    socket_manager.tournaments_received.connect(handle_tournaments)
    socket_manager.tournament_data_received.connect(handle_final_data)

    # 2. Network & License Check
    loader = StartupLoaderDialog(license_manager)
    loader.start_check()
    loader.exec_()
    
    is_offline_mode = loader.is_offline_mode
    
    # NEW: If server is up but no license, force activation
    if not is_offline_mode and loader.needs_activation:
        act_dialog = LicenseDialog(license_manager)
        if act_dialog.exec_() != QDialog.Accepted:
            # If they cancel activation, we can either exit or force offline
            print("Activation cancelled. Switching to offline.")
            is_offline_mode = True

    # 3. Wait for Tournament Data (Only if Online)
    if is_offline_mode:
        print("Starting in FREE OFFLINE mode.")
    else:
        # ONLINE MODE
        wait_loop = QtNativeLoop()
        # socket_manager.connect() is triggered by license_manager.connection_ready
        if not hasattr(socket_manager, 'tournament_data') or socket_manager.tournament_data is None:
            print("Waiting for server response...")
            wait_loop.exec_() 

    # 4. Proceed to Main Window
    main_window = MainWindow()
    status_text = " (OFFLINE)" if is_offline_mode else " (ONLINE)"
    main_window.setWindowTitle(f"TrueVAR {status_text}")
    main_window.show()

    with event_loop:
        event_loop.run_forever()

if __name__ == '__main__':
    main()