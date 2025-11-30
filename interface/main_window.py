# interface/main_window.py
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QLabel, QMessageBox
from PyQt5.QtCore import QTimer, Qt, pyqtSlot
from PyQt5.QtGui import QKeySequence, QFont
from interface.main_screen import MainScreen
from interface.settings.settings_screen import SettingsScreen
from interface.replay_screen import ReplayScreen
from time import time

from app.injector import Injector
from app.udp_manager import UdpManager
from app.obs_manager import OBSManager
from app.external_screen_manager import ExternalScreenManager
from app.key_bind_manager import KeyBindManager
from app.webserver_manager import WebServerManager
from app.camera_manager import CameraManager
from app.main_manager import MainManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.key_bind_manager: KeyBindManager = Injector.find(KeyBindManager)
        self.obs_manager: OBSManager = Injector.find(OBSManager)
        self.camera_manager: CameraManager = Injector.find(CameraManager)
        self.udp_manager: UdpManager = Injector.find(UdpManager)
        self.external_screen_manager: ExternalScreenManager = Injector.find(ExternalScreenManager)

        if self.udp_manager.udp_default and not self.udp_manager.thread.isRunning():
            self.udp_manager.start_listener()

        # Create the stacked layout
        self.stacked_widget = QStackedWidget(self)

        # Create instances of each screen
        self.main_screen = MainScreen()
        self.settings_screen = SettingsScreen()
        self.replay_screen = ReplayScreen()
        self.current_screen = 0

        self.screen_manager: MainManager = Injector.find(MainManager)
        self.screen_manager.show_settings_signal.connect(self.show_settings)
        self.screen_manager.hide_settings_signal.connect(self.hide_settings)
        self.screen_manager.show_replay_signal.connect(self.show_replay)
        self.screen_manager.hide_replay_signal.connect(self.hide_replay)
        self.screen_manager.toggle_recording_signal.connect(self.toggle_recording)

        # Add screens to the stacked widget
        self.stacked_widget.addWidget(self.main_screen)
        self.stacked_widget.addWidget(self.settings_screen)
        self.stacked_widget.addWidget(self.replay_screen)

        # Set the first screen as the main screen
        self.stacked_widget.setCurrentWidget(self.main_screen)

        self.screen_indicator_label = QLabel("Mirroring the screen", self)
        self.screen_indicator_label.setAlignment(Qt.AlignCenter)
        self.screen_indicator_label.setFont(QFont("Arial", 10))
        self.screen_indicator_label.setStyleSheet("""
            QLabel {
                color: black; 
                background-color: white; 
                border: 1px solid black; 
                border-radius: 2px; 
                padding: 5px 10px;
            }
        """)
        self.screen_indicator_label.setVisible(False) # Start hidden
        
        # Connect the manager's state change signal to the new slot
        self.external_screen_manager.screen_changed_mirror.connect(self.update_screen_indicator)

        self.toast_label = QLabel("", self)
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.setFont(QFont("Arial", 14))
        self.toast_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 0.7); padding: 10px;")
        self.toast_label.setVisible(False)

        self.setCentralWidget(self.stacked_widget)

        # self.toggle_fullscreen()

        self.resizeEvent(None)

    def show_main(self):
        # self.main_screen.update_camera_list()
        self.stacked_widget.setCurrentWidget(self.main_screen)

    def keyPressEvent(self, event):
        key_sequence = QKeySequence(event.modifiers() | event.key())

        if key_sequence == QKeySequence("F11"):
            self.toggle_fullscreen()

        # Open settings or replay screen based on key press
        if key_sequence == QKeySequence(self.key_bind_manager.settings_key):
            if self.current_screen == 0:
                self.show_settings()

            elif self.current_screen == 1:
                self.hide_settings()

        if key_sequence == QKeySequence(self.key_bind_manager.replay_key):
            if self.current_screen == 0:
                self.show_replay()

            elif self.current_screen == 2:
                self.hide_replay()
                if self.external_screen_manager.is_mirror:
                    self.external_screen_manager.toggle_display_mode()

        if key_sequence == QKeySequence(self.key_bind_manager.record_key) and self.current_screen == 0:
            self.toggle_recording()

        if key_sequence == QKeySequence(self.key_bind_manager.toggle_external_screen_key):
            self.external_screen_manager.toggle_display_mode()

        if key_sequence == QKeySequence(self.key_bind_manager.set_troubleshooting_scene):
            self.obs_manager.set_troubleshooting_scene()
                
        if key_sequence == QKeySequence(self.key_bind_manager.next_camera_key) and self.current_screen == 2:
            self.replay_screen.next_page()

        if key_sequence == QKeySequence(self.key_bind_manager.play_pause_key) and self.current_screen == 2:
            self.replay_screen.play_video()

        if key_sequence == QKeySequence(self.key_bind_manager.frame_forward_key) and self.current_screen == 2:
            self.replay_screen.frame_forward()

        if key_sequence == QKeySequence(self.key_bind_manager.frame_backward_key) and self.current_screen == 2:
            self.replay_screen.frame_backward()

        if key_sequence == QKeySequence(self.key_bind_manager.second_forward_key) and self.current_screen == 2:
            self.replay_screen.sec_forward()

        if key_sequence == QKeySequence(self.key_bind_manager.second_backward_key) and self.current_screen == 2:
            self.replay_screen.sec_backward()

        if key_sequence == QKeySequence(self.key_bind_manager.reset_zoom_key) and self.current_screen == 2:
            self.replay_screen.videoWidget.zoom_reset()

    def show_settings(self):
        if not self.camera_manager.is_recording:
            self.settings_screen.start()
            self.stacked_widget.setCurrentWidget(self.settings_screen)
            self.current_screen = 1
        else:
            self.show_toast_message("Settings can't be open while recording")

    def hide_settings(self):
        self.settings_screen.stop()
        self.show_main()
        self.current_screen = 0

    def show_replay(self):
        if self.camera_manager.is_recording:
            self.camera_manager.stop_cameras()
            self.replay_screen.start()
            self.stacked_widget.setCurrentWidget(self.replay_screen)
            self.current_screen = 2

            # pro webserver implementation
            self.obs_manager.set_ivr_scene()
        else:
            self.show_toast_message("Video Replay can't be open without recording")

    def hide_replay(self):
        self.camera_manager.new_segment()
        self.camera_manager.start_cameras()
        self.show_main()
        self.current_screen = 0

        # pro webserver implementation
        self.obs_manager.set_main_scene()

    def toggle_recording(self):
        if not self.camera_manager.is_recording:
            self.start_recording()
        
        else:
            self.stop_recording()

    def start_recording(self):
        if not self.camera_manager.is_recording:
            if self.camera_manager.error_while_shm:
                self.show_toast_message("No video input selected")
                return
        
            self.camera_manager.release_records()
            self.camera_manager.reset_segments()

            self.camera_manager.fight_num = str(time())[6: 12]
            self.camera_manager.start_cameras()

    def stop_recording(self):
        if self.camera_manager.is_recording:
            self.camera_manager.stop_cameras()
            self.camera_manager.save_for_ai()

    def toggle_fullscreen(self):
        # If the window is already fullscreen, go back to normal
        if self.isFullScreen():
            self.showNormal()  # Exit fullscreen
        else:
            self.showFullScreen()  # Enter fullscreen

    @pyqtSlot(bool)
    def update_screen_indicator(self, is_mirror):
        """Show or hide the 'Showing to coaches' indicator."""
        self.screen_indicator_label.setVisible(is_mirror)
        # Repositioning is handled in resizeEvent
        if is_mirror and self.current_screen == 2:
            self.obs_manager.set_ivr_closeup_scene()

    # --- NEW: Override resizeEvent to reposition the indicator ---
    def resizeEvent(self, event):
        """Repositions the indicator label when the window size changes."""
        
        # Make sure the indicator is positioned correctly in the top-right corner
        self.screen_indicator_label.adjustSize()
        
        # Calculate position: top-right corner with a 10px margin
        x = self.width() - self.screen_indicator_label.width() - 16
        y = 48
        
        self.screen_indicator_label.move(x, y)
        
        # Also reposition the toast label if needed (good practice for resize)
        self.toast_label.move(
            (self.width() - self.toast_label.width()) // 2,
            (self.height() - self.toast_label.height()) // 2
        )

        super().resizeEvent(event)

    def show_toast_message(self, message):
        """Show a temporary toast message."""
        self.toast_label.setText(message)
        self.toast_label.adjustSize()
        self.toast_label.move(
            (self.width() - self.toast_label.width()) // 2,
            (self.height() - self.toast_label.height()) // 2
        )
        self.toast_label.setVisible(True)

        # Hide the toast after 2 seconds
        QTimer.singleShot(2000, lambda: self.toast_label.setVisible(False))

    def closeEvent(self, event):
        # Stop all video streams on exit
        self.camera_manager.stop()
        self.settings_screen.stop()
        super().closeEvent(event)