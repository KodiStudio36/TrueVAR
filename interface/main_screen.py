from app.injector import Injector
from app.camera_manager import CameraManager
from app.main_manager import MainManager

from interface.settings.widgets.video_stream_widget import VideoStreamWidget

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QHBoxLayout,
    QFrame, QSizePolicy, QScrollArea, QPushButton, QLineEdit
)
from PyQt5.QtCore import Qt


class MainScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.camera_manager: CameraManager = Injector.find(CameraManager)
        self.blink_timers = {}
        self.video_widgets = []
        self.init_ui()
        self.start()

    def init_ui(self):
        vertical = QVBoxLayout()
        vertical.setContentsMargins(0, 0, 0, 0)

        # --- Top green toolbar ---
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(5)

        # Left button
        left_btn = QPushButton("Button")
        toolbar_layout.addWidget(left_btn, alignment=Qt.AlignLeft)

        # Center text input + button
        text_input = QLabel("some text here")
        text_input.setFixedWidth(200)
        toolbar_layout.addWidget(text_input, alignment=Qt.AlignLeft)

        toolbar_layout.addStretch()

        self.recording_btn = QPushButton("Start Recording")
        toolbar_layout.addWidget(self.recording_btn, alignment=Qt.AlignRight)

        # Stretch before settings

        # Right settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedWidth(30)
        settings_btn.clicked.connect(lambda: Injector.find(MainManager).show_settings())
        toolbar_layout.addWidget(settings_btn, alignment=Qt.AlignRight)

        vertical.addWidget(toolbar, stretch=0)

        # --- Top status area ---
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        my_layout = QGridLayout(frame)
        my_layout.setContentsMargins(0, 0, 0, 0)

        self.status_label = QLabel("TrueVAR is not recording")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 36px;")
        my_layout.addWidget(self.status_label, 0, 0)

        vertical.addWidget(frame, stretch=1)

        # --- Scrollable camera previews ---
        # scroll_area = QScrollArea()
        # scroll_area.setWidgetResizable(True)
        # scroll_area.setMinimumHeight(200)


        # container = QFrame()
        # container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        # my_layout1 = QHBoxLayout(container)
        # my_layout1.setContentsMargins(0, 0, 0, 0)

        # for idx in range(self.camera_manager.camera_count + 1):
        #     preview_label = VideoStreamWidget(
        #         f"{self.camera_manager.get_shmsink(idx)} "
        #         f"! video/x-raw,width={'640' if idx == 0 else self.camera_manager.res_width},"
        #         f"height={'480' if idx == 0 else self.camera_manager.res_height},"
        #         f"framerate={self.camera_manager.fps}/1,format=NV12 ! videoconvert ! videoscale "
        #         f"! video/x-raw,format=RGB,width=272,height=153 ! queue ! "
        #         f"appsink name=sink emit-signals=True sync=True drop=False",
        #         272, 153
        #     )
        #     self.video_widgets.append(preview_label)
        #     my_layout1.addWidget(preview_label)

        # scroll_area.setWidget(container)

        # vertical.addWidget(scroll_area, stretch=0)

        self.setLayout(vertical)

        # connect recording status
        self.camera_manager.is_recording_stream.connect(
            lambda is_recording:
                self.update_status(is_recording)
        )

    def update_status(self, is_recording):
        if is_recording:
            self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 36px;")
            self.status_label.setText("TrueVAR is recording")
            self.recording_btn.setText("Stop Recording")
        else:
            self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 36px;")
            self.status_label.setText("TrueVAR is not recording")
            self.recording_btn.setText("Start Recording")

    def start(self):
        for widget in self.video_widgets:
            widget.start()

    def stop(self):
        for widget in self.video_widgets:
            widget.stop()
