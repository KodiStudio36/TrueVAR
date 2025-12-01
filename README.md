TrueVAR Documentation
==========================



## PC Instalation

Boot linux ISO file (arcolinuxb-i3-v24.03.01-x86_64.iso) using USB (hold f7).

### ISO File Instalation

After boot select easy instalation (offline):
1. Location
    - `Europe`
    - `Bratislava`
2. Keyboard
    - `Slovak (QWERTZ)`
3. User
    - hostname: `truevar`
    - username: `turevar`
    - password: `TaekwondoVAR`
    - [x] `Auto login on start`
    - [x] `Use same password for root`
4. Partiton
    - [x] `Erase Memory`
5. Finish
    - [x] `Reboot PC`

### ArcoLinux discontinuation

ArcoLinux is depricated so we need to update mirrors so the PackageManager (pacman) can update system and install new packages.

After reboot select `update mirrors`.
```
sudo pacman -Sy archlinux-keyring
sudo pacman -Suy
```

If an error occurs due to linux-firmware-nvidia when updating the operating system, do the following:
```
sudo pacman -R linux-firmware
sudo pacman -Suy linux-firmware
```

### Install TrueVAR

Install necessary packages for vaapi to work.

    sudo pacman -S gstreamer-vaapi libva libva-utils intel-media-driver

Clone TrueVAR from GitHub
```
cd Documents
git clone https://github.com/KodiStudio36/TrueVAR.git
```
Install necessary python libraries
```
cd TrueVAR
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Make TrueVAR autostart on login
```
cd ~
echo "exec /home/truevar/Documents/TrueVAR/autostart_main.sh &" >> ~/.config/i3/config
```

### Install ShuttleExpress

Install necessary packages.

    sudo pacman -S go xdotool

Clone shuttle-go from GitHub
```
cd Documents
git clone https://github.com/abourget/shuttle-go.git
```
Build the project
```
cd shuttle-go
go build -o shuttle-go
```
Give user necessary privileges

    sudo usermod -aG input $USER

Put settings file from TrueVAR to home directory
```
cd ~
cp ~/Documents/TrueVAR/shuttle-go/.shuttle-go.json .
```

#### Make shuttle-go start on device plug in

create service for shuttle-go

    nano ~/.config/systemd/user/shuttle-go.service

If an error occurs due to non existing directory, do the following and repeat the command:

    mkdir -p ~/.config/systemd/user

~/.config/systemd/user/shuttle-go.service
```
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
```
create udev rule

    sudo nano /etc/udev/rules.d/99-shuttle-go.rules

/etc/udev/rules.d/99-shuttle-go.rules
```
# Start user service when device is added
ACTION=="add", ATTRS{idVendor}=="0b33", ATTRS{idProduct}=="0020", TAG+="systemd", ENV{SYSTEMD_USER_WANTS}="shuttle-go.service"

# Stop user service when device is removed
ACTION=="remove", ATTRS{idVendor}=="0b33", ATTRS{idProduct}=="0020", RUN+="/bin/loginctl enable-linger truevar; /usr/bin/sudo -u truevar systemctl --user stop shuttle-go.service"
```
reload udev rules
```
sudo udevadm control --reload-rules
sudo udevadm trigger
```
if it doesn't work, debug with

    systemctl --user status shuttle-go.service

### Set permanent static IP address

stop network manager
```
sudo nmcli device set enp3s0 managed no
sudo systemctl stop NetworkManager
```
and replace it with networkd
```
sudo systemctl enable systemd-networkd
sudo systemctl start systemd-networkd
```
create a new network rule

    sudo nano /etc/systemd/network/20-ethernet.network

/etc/systemd/network/20-ethernet.network
```
[Match]
Name=enp3s0

[Network]
Address=192.168.0.$uniqe$/24
Gateway=192.168.0.1
DNS=8.8.8.8
```
restart networkd

    sudo systemctl restart systemd-networkd

and reanable network manager
```
sudo systemctl start NetworkManager
sudo systemctl enable systemd-networkd
```
The End

### OBS

```
yay -S obs-studio-browser
sudo pacman -S obs-gstreamer
```