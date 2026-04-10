import sys
import socket
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QGroupBox, QGridLayout, 
                             QTextEdit, QSpinBox)
from PyQt5.QtCore import Qt

class UdpTester(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TrueVAR UDP Protocol Tester")
        self.resize(450, 750) # Increased height slightly

        # Network Settings
        self.ip = "127.0.0.1"
        self.port = 8000 # Adjusted to match your server default
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- Connection Settings ---
        conn_group = QGroupBox("Target Settings")
        conn_layout = QHBoxLayout()
        
        self.ip_input = QLineEdit(self.ip)
        self.port_input = QLineEdit(str(self.port))
        
        conn_layout.addWidget(QLabel("IP:"))
        conn_layout.addWidget(self.ip_input)
        conn_layout.addWidget(QLabel("Port:"))
        conn_layout.addWidget(self.port_input)
        conn_group.setLayout(conn_layout)
        main_layout.addWidget(conn_group)

        # --- Match Setup ---
        setup_group = QGroupBox("1. Match Setup")
        setup_layout = QGridLayout()

        self.blue_name = QLineEdit("Blue Player")
        self.blue_nat = QLineEdit("USA") 
        self.red_name = QLineEdit("Red Player")
        self.red_nat = QLineEdit("KOR") 

        btn_init_match = QPushButton("Init Match Data (mch)")
        btn_init_match.clicked.connect(self.send_init_match)
        
        btn_set_fighters = QPushButton("Set Fighters (at1)")
        btn_set_fighters.clicked.connect(self.send_fighters)

        setup_layout.addWidget(QLabel("Blue:"), 0, 0)
        setup_layout.addWidget(self.blue_name, 0, 1)
        setup_layout.addWidget(self.blue_nat, 0, 2)
        setup_layout.addWidget(QLabel("Red:"), 1, 0)
        setup_layout.addWidget(self.red_name, 1, 1)
        setup_layout.addWidget(self.red_nat, 1, 2)
        setup_layout.addWidget(btn_init_match, 2, 0, 1, 3)
        setup_layout.addWidget(btn_set_fighters, 3, 0, 1, 3)
        
        setup_group.setLayout(setup_layout)
        main_layout.addWidget(setup_group)

        # --- Round Control ---
        round_group = QGroupBox("2. Round Control")
        round_layout = QGridLayout()

        # Added Round Number Control
        self.rnd_spin = QSpinBox()
        self.rnd_spin.setRange(1, 10)
        self.rnd_spin.setValue(1)
        
        btn_set_rnd = QPushButton("Set Round (rnd)")
        btn_set_rnd.clicked.connect(self.send_round_number)

        self.time_input = QLineEdit("02:00")
        self.time_input.setAlignment(Qt.AlignCenter)

        btn_start = QPushButton("Start Round")
        btn_start.setStyleSheet("background-color: #d4edda; color: green;")
        btn_start.clicked.connect(self.send_round_start)

        btn_pause = QPushButton("Pause (Kye-shi)")
        btn_pause.clicked.connect(self.send_pause)

        btn_end = QPushButton("End Round (Break)")
        btn_end.setStyleSheet("background-color: #f8d7da; color: red;")
        btn_end.clicked.connect(self.send_round_end)

        # Layout organization
        round_layout.addWidget(QLabel("Round #:"), 0, 0)
        round_layout.addWidget(self.rnd_spin, 0, 1)
        round_layout.addWidget(btn_set_rnd, 0, 2)
        
        round_layout.addWidget(QLabel("Clock Time:"), 1, 0)
        round_layout.addWidget(self.time_input, 1, 1)
        
        round_layout.addWidget(btn_start, 2, 0)
        round_layout.addWidget(btn_pause, 2, 1)
        round_layout.addWidget(btn_end, 2, 2)
        
        round_group.setLayout(round_layout)
        main_layout.addWidget(round_group)

        # --- Scoring ---
        score_group = QGroupBox("3. Scoring Simulation")
        score_layout = QGridLayout()

        btn_blue_punch = QPushButton("Blue Punch")
        btn_blue_punch.clicked.connect(lambda: self.send_hit("blue", 1))
        btn_blue_trunk = QPushButton("Blue Trunk")
        btn_blue_trunk.setStyleSheet("background-color: #cce5ff;")
        btn_blue_trunk.clicked.connect(lambda: self.send_hit("blue", 2))
        btn_blue_head = QPushButton("Blue Head")
        btn_blue_head.clicked.connect(lambda: self.send_hit("blue", 3))
        
        btn_red_punch = QPushButton("Red Punch")
        btn_red_punch.clicked.connect(lambda: self.send_hit("red", 1))
        btn_red_trunk = QPushButton("Red Trunk")
        btn_red_trunk.setStyleSheet("background-color: #f8d7da;")
        btn_red_trunk.clicked.connect(lambda: self.send_hit("red", 2))
        btn_red_head = QPushButton("Red Head")
        btn_red_head.clicked.connect(lambda: self.send_hit("red", 3))

        self.blue_score_spin = QSpinBox()
        self.red_score_spin = QSpinBox()
        self.blue_score_spin.setRange(0, 99)
        self.red_score_spin.setRange(0, 99)
        
        btn_update_score = QPushButton("Update Score (sc1)")
        btn_update_score.clicked.connect(self.send_score_update)

        score_layout.addWidget(QLabel("<b>Blue</b>"), 0, 0)
        score_layout.addWidget(QLabel("<b>Red</b>"), 0, 1)
        score_layout.addWidget(btn_blue_punch, 1, 0)
        score_layout.addWidget(btn_red_punch, 1, 1)
        score_layout.addWidget(btn_blue_trunk, 2, 0)
        score_layout.addWidget(btn_red_trunk, 2, 1)
        score_layout.addWidget(btn_blue_head, 3, 0)
        score_layout.addWidget(btn_red_head, 3, 1)
        score_layout.addWidget(QLabel("Points:"), 4, 0)
        score_layout.addWidget(self.blue_score_spin, 5, 0)
        score_layout.addWidget(self.red_score_spin, 5, 1)
        score_layout.addWidget(btn_update_score, 6, 0, 1, 2)

        score_group.setLayout(score_layout)
        main_layout.addWidget(score_group)

        # --- Match Result ---
        win_group = QGroupBox("4. Match Result")
        win_layout = QHBoxLayout()
        btn_win_blue = QPushButton("Blue Wins")
        btn_win_blue.setStyleSheet("background-color: blue; color: white; font-weight: bold;")
        btn_win_blue.clicked.connect(lambda: self.send_winner("blue"))
        btn_win_red = QPushButton("Red Wins")
        btn_win_red.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        btn_win_red.clicked.connect(lambda: self.send_winner("red"))
        win_layout.addWidget(btn_win_blue)
        win_layout.addWidget(btn_win_red)
        win_group.setLayout(win_layout)
        main_layout.addWidget(win_group)

        # --- Log ---
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(100)
        main_layout.addWidget(QLabel("Sent Packets Log:"))
        main_layout.addWidget(self.log_output)

        self.setLayout(main_layout)

    # --- Senders ---

    def send_packet(self, message):
        target_ip = self.ip_input.text()
        try:
            target_port = int(self.port_input.text())
            self.sock.sendto(message.encode('utf-8'), (target_ip, target_port))
            self.log_output.append(f"-> {message}")
            sb = self.log_output.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception as e:
            self.log_output.append(f"Error: {e}")

    def send_round_number(self):
        """Sends the current value of the round spinbox."""
        msg = f"rnd;{self.rnd_spin.value()}"
        self.send_packet(msg)

    def send_init_match(self):
        # Now uses the current spinbox value instead of hardcoded 1
        msg = "mch;101;Test Match;Men-80kg;0;0;0;0;0;0;0;0;0;0;2" 
        self.send_packet(msg)
        self.send_round_number()

    def send_fighters(self):
        b_name = self.blue_name.text()
        b_nat = self.blue_nat.text()
        r_name = self.red_name.text()
        r_nat = self.red_nat.text()
        msg = f"at1;{b_name};0;{b_nat};0;{r_name};0;{r_nat}"
        self.send_packet(msg)

    def send_round_start(self):
        current_time = self.time_input.text()
        msg = f"clk;{current_time};start"
        self.send_packet(msg)

    def send_pause(self):
        current_time = self.time_input.text()
        msg = f"ij0;{current_time}" 
        self.send_packet(msg)

    def send_round_end(self):
        msg = "brk;00:00"
        self.send_packet(msg)

    def send_hit(self, color, level):
        cmd = "pt1" if color == "blue" else "pt2"
        msg = f"{cmd};{level}"
        self.send_packet(msg)

    def send_score_update(self):
        b_score = self.blue_score_spin.value()
        r_score = self.red_score_spin.value()
        msg = f"sc1;{b_score};0;{r_score}"
        self.send_packet(msg)

    def send_winner(self, color):
        msg = f"win;{color}"
        self.send_packet(msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tester = UdpTester()
    tester.show()
    sys.exit(app.exec_())