import sys, os, asyncio
from PyQt5.QtWidgets import QApplication, QDialog
from app.tournament_manager import TournamentManager
from interface.main_window import MainWindow
from interface.dialogs.license_dialog import LicenseDialog
from interface.dialogs.tournament_dialog import TournamentSelectionDialog
from app.license_manager import LicenseManager
from app.socket_manager import SocketManager  # <-- New Import
from app.injector import Injector
from app.udp_manager import UdpManager
from config import records_path, settings_path # Ensure socket_url is in config

from qasync import QEventLoop as AsyncioPyQtLoop 
from PyQt5.QtCore import QEventLoop as QtNativeLoop

def main():
    app = QApplication(sys.argv)

    # 1. Setup the asyncio/PyQt bridge
    event_loop = AsyncioPyQtLoop(app)
    asyncio.set_event_loop(event_loop)

    os.makedirs(records_path, exist_ok=True)
    os.makedirs(settings_path, exist_ok=True)

    # # Initialize Managers
    # license_manager = Injector.find(LicenseManager)
    # socket_manager = Injector.find(SocketManager)
    # tournament_manager = Injector.find(TournamentManager)

    # # --- GLUE LOGIC ---
    # # When license is verified (online or offline), tell socket to connect
    # license_manager.connection_ready.connect(socket_manager.connect)

    # def handle_tournaments(names, max_courts):
    #     sel_dialog = TournamentSelectionDialog(names, max_courts)
        
    #     if sel_dialog.exec_() == QDialog.Accepted:
    #         # Unpack both the name and the spinbox value
    #         choice_name, choice_court = sel_dialog.get_selection()
    #         print(f"Selecting {choice_name} on Court {choice_court}")
            
    #         # Send both to the server
    #         socket_manager.select_tournament(choice_name, choice_court)
    #     else:
    #         sys.exit(0)

    # def handle_final_data(_):
    #     print(_)
    #     # Store data locally so the check below sees it
    #     wait_loop.quit() 

    # # Listen to SocketManager instead of LicenseManager
    # socket_manager.tournaments_received.connect(handle_tournaments)
    # socket_manager.tournament_data_received.connect(handle_final_data)

    # # 2. License Check (Blocking Dialog)
    # is_valid = license_manager.validate()
    # if not is_valid:
    #     # Pass both if the dialog needs to trigger socket connection on manual activation
    #     dialog = LicenseDialog(license_manager) 
    #     if dialog.exec_() != QDialog.Accepted:
    #         sys.exit(0)

    # # 3. Wait for Tournament Data
    # wait_loop = QtNativeLoop()
    
    # # Check socket_manager for data now
    # if not hasattr(socket_manager, 'tournament_data') or socket_manager.tournament_data is None:
    #     print("Waiting for tournament configuration via SocketIO...")
    #     # Note: If validation was local/offline, you might need a timeout here 
    #     # or logic to handle offline mode if the server is unreachable.
    #     wait_loop.exec_() 

    # 4. Proceed to Main Window
    main_window = MainWindow()
    
    main_window.setWindowTitle("TrueVAR")
    main_window.show()

    # 5. Background Services
    udp_manager: UdpManager = Injector.find(UdpManager)
    if udp_manager.udp_default and not udp_manager.thread.isRunning():
        udp_manager.start_listener()

    with event_loop:
        event_loop.run_forever()

if __name__ == '__main__':
    main()