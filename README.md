plug usb with arco linux
hold f7 key to open bootloader on acemagic mini pc
select boot usb

select easy instalation no network
location: Europe, Bratislava
keyboard: Slovak (QWERTZ)
hostname: truevar
username: turevar
password: TaekwondoVAR
Auto login on start
Same password for root
reboot
update mirrors

sudo pacman -Sy archlinux-keyring
sudo pacman -Suy

if error with linux-firmware-nvidia do:
sudo pacman -R linux-firmware
sudo pacman -Suy linux-firmware

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


