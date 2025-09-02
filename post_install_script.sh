cd Documents
git clone https://github.com/KodiStudio36/TrueVAR.git
cd TrueVAR
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir records
sudo pacman -S gstreamer-vaapi libva libva-utils intel-media-driver
cd ..
echo "exec /home/truevar/Documents/TrueVAR/autostart_main.sh &" >> .config/i3/config

sudo pacman -S go xdotool
git clone https://github.com/abourget/shuttle-go.git
cd shuttle-go
go build -o shuttle-go
sudo usermod -aG input $USER
cd ~
cp Documents/TrueVAR/shuttle-go/.shuttle-go.json .

sudo nmcli device set enp3s0 managed no
sudo systemctl stop NetworkManager
sudo systemctl enable systemd-networkd
sudo systemctl start systemd-networkd
sudo nano /etc/systemd/network/20-ethernet.network

[Match]
Name=enp3s0

[Network]
Address=192.168.0.$uniqe$/24
Gateway=192.168.0.1
DNS=8.8.8.8

sudo systemctl restart systemd-networkd
sudo networkctl status enp3s0
sudo systemctl start NetworkManager
sudo systemctl enable systemd-networkd


mkdir ~/.config/systemd
mkdir ~/.config/systemd/user
nano ~/.config/systemd/user/shuttle-go.service

[Unit]
Description=ShuttleGO Daemon
After=graphical.target

[Service]
Type=simple
WorkingDirectory=/home/truevar
ExecStart=/home/truevar/Documents/shuttle-go/shuttle-go /dev/input/by-id/usb-Contour_Design_ShuttleXpress-event-mouse
Restart=on-failure
Environment=DISPLAY=:0

[Install]
WantedBy=default.target

sudo nano /etc/udev/rules.d/99-shuttle-go.rules

ACTION=="add", SUBSYSTEM=="input", ATTRS{name}=="Contour Design ShuttleXpress", TAG+="systemd", ENV{SYSTEMD_WANTS}="shuttle-go.service"
ACTION=="remove", SUBSYSTEM=="input", ATTRS{name}=="Contour Design ShuttleXpress", TAG+="systemd", ENV{SYSTEMD_WANTS}="shuttle-go.service"

sudo udevadm control --reload-rules
sudo udevadm trigger

systemctl --user status shuttle-go.service
journalctl --user -u shuttle-go.service -f
