# interface/main_window.py
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QLabel, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeySequence, QFont
from interface.main_screen import MainScreen
from interface.settings_screen import SettingsScreen
from interface.replay_screen import ReplayScreen
from time import time

from app.injector import Injector
from app.webserver_manager import WebServerManager
from app.key_bind_manager import KeyBindManager
from app.camera_manager import CameraManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.key_bind_manager: KeyBindManager = Injector.find(KeyBindManager)
        webserver_manager: WebServerManager = Injector.find(WebServerManager)
        webserver_manager.set_context(self)
        self.camera_manager: CameraManager = Injector.find(CameraManager)

        # Create the stacked layout
        self.stacked_widget = QStackedWidget(self)

        # Create instances of each screen
        self.main_screen = MainScreen()
        self.settings_screen = SettingsScreen()
        self.replay_screen = ReplayScreen()
        self.current_screen = 0

        # Add screens to the stacked widget
        self.stacked_widget.addWidget(self.main_screen)
        self.stacked_widget.addWidget(self.settings_screen)
        self.stacked_widget.addWidget(self.replay_screen)

        # Set the first screen as the main screen
        self.stacked_widget.setCurrentWidget(self.main_screen)

        self.toast_label = QLabel("", self)
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.setFont(QFont("Arial", 14))
        self.toast_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 0.7); padding: 10px;")
        self.toast_label.setVisible(False)

        self.setCentralWidget(self.stacked_widget)

        self.toggle_fullscreen()

    def show_main(self):
        # self.main_screen.update_camera_list()
        self.stacked_widget.setCurrentWidget(self.main_screen)

    def show_settings(self):
        self.settings_screen.start()
        self.stacked_widget.setCurrentWidget(self.settings_screen)

    def show_replay(self):
        self.replay_screen.start()
        self.stacked_widget.setCurrentWidget(self.replay_screen)

    def keyPressEvent(self, event):
        key_sequence = QKeySequence(event.modifiers() | event.key())

        if key_sequence == QKeySequence("F11"):
            self.toggle_fullscreen()

        # Open settings or replay screen based on key press
        if key_sequence == QKeySequence(self.key_bind_manager.settings_key):
            if self.current_screen == 0:
                if not self.camera_manager.is_recording:
                    self.show_settings()
                    self.current_screen = 1
                else:
                    self.show_toast_message("Settings can't be open while recording")

            elif self.current_screen == 1:
                self.settings_screen.stop()
                self.show_main()
                self.current_screen = 0

        if key_sequence == QKeySequence(self.key_bind_manager.replay_key):
            if self.current_screen == 0:
                if self.camera_manager.is_recording:
                    self.camera_manager.stop_cameras()
                    self.show_replay()
                    self.current_screen = 2

                    # pro webserver implementation
                    Injector.find(WebServerManager).start_ivr_scene()
                else:
                    self.show_toast_message("Video Replay can't be open without recording")

            elif self.current_screen == 2:
                self.camera_manager.new_segment()
                self.camera_manager.start_cameras()
                self.show_main()
                self.current_screen = 0

                # pro webserver implementation
                Injector.find(WebServerManager).end_ivr_scene()

        if key_sequence == QKeySequence(self.key_bind_manager.record_key) and self.current_screen == 0:
            if not self.camera_manager.is_recording:
                self.start_recording()
            
            else:
                self.stop_recording()
                

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

    def isStopRecording(self):
        qmb = QMessageBox()
        qmb.setWindowTitle("Stop recording")
        qmb.setText("Are you sure you want to stop recording?")

        qmb.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        qmb.button(QMessageBox.Ok).setText("Yes, stop recording")
        qmb.button(QMessageBox.Cancel).setText("Cancel")

        if qmb.exec() == QMessageBox.Ok:
            return True
        else:
            return False

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