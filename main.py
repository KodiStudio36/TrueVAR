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
from app.udp_manager import UdpManager
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

    def handle_tournaments(names, max_courts):
        sel_dialog = TournamentSelectionDialog(names, max_courts)
        if sel_dialog.exec_() == QDialog.Accepted:
            choice_name, choice_court = sel_dialog.get_selection()
            socket_manager.select_tournament(choice_name, choice_court)
        else:
            sys.exit(0)

    def handle_final_data(_):
        wait_loop.quit() 

    socket_manager.tournaments_received.connect(handle_tournaments)
    socket_manager.tournament_data_received.connect(handle_final_data)

    # 2. Network Check (The Loader Dialog handles everything now)
    loader = StartupLoaderDialog(license_manager)
    loader.start_check()
    
    # This will now always eventually return Accepted 
    # unless the user closes the app process entirely.
    loader.exec_()
    is_offline_mode = loader.is_offline_mode

    # 3. Wait for Tournament Data
    if is_offline_mode:
        print("Starting in FREE OFFLINE mode.")
        # Logic for offline: Perhaps load a 'default' tournament or empty state
    else:
        # ONLINE MODE: We must wait for the server to send tournament data
        wait_loop = QtNativeLoop()
        if not hasattr(socket_manager, 'tournament_data') or socket_manager.tournament_data is None:
            print("Waiting for server response...")
            # We add a small safety timeout here so it doesn't hang forever 
            # if the socket connection fails after the initial check.
            wait_loop.exec_() 

    # 4. Proceed to Main Window
    main_window = MainWindow()
    status_text = " (OFFLINE)" if is_offline_mode else " (ONLINE)"
    main_window.setWindowTitle(f"TrueVAR {status_text}")
    main_window.show()

    # 5. Background Services
    udp_manager: UdpManager = Injector.find(UdpManager)
    if udp_manager.udp_default and not udp_manager.thread.isRunning():
        udp_manager.start_listener()

    with event_loop:
        event_loop.run_forever()

if __name__ == '__main__':
    main()