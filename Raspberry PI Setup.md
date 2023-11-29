# Steps to Create Lightbar RPI
## Starting Environment
Raspberry Pi Zero 2 W
```bash
cat /etc/os-release
```
```
PRETTY_NAME="Raspbian GNU/Linux 11 (bullseye)"
NAME="Raspbian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"
```

```bash
sudo apt update
sudo apt upgrade
```

## Creating Hotspot
**Need to attach ethernet somewhere to the PI or else the steps after are impossible**

Instructions from [this article](https://www.stevemurch.com/setting-up-a-raspberry-pi-for-ad-hoc-networking-tech-note/2022/12)
```bash
sudo apt install hostapd

sudo systemctl unmask hostapd
sudo systemctl enable hostapd

sudo apt install dnsmasq

sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent
```
```bash
sudo nano /etc/dhcpcd.conf
```
```conf
# Add to end of file
interface wlan0
    static ip_address=192.168.11.1/24
    nohook wpa_supplicant
```
```bash
sudo nano /etc/sysctl.d/routed-ap.conf
```
```conf
# In new file
# Enable IPv4 routing
net.ipv4.ip_forward=1
```
```bash
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo netfilter-persistent save
```
```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```
Adjust `address` as needed
```conf
# In new file
interface=wlan0
dhcp-range=192.168.11.2,192.168.11.20,255.255.255.0,24h
domain=wlan
address=/gw.wlan/192.168.11.1
```
```bash
sudo rfkill unblock wlan
```
```bash
sudo nano /etc/hostapd/hostapd.conf
```
Adjust `ssid` and `wpa_passphrase` as needed
```conf
country_code=US
interface=wlan0
ssid=RPI
hw_mode=g
channel=7
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=SomePassword
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```
```bash
sudo systemctl reboot
```
## Adding Swap
Supposedly very bad for the life of SD cards but very much needed
```bash
sudo dphys-swapfile swapoff
```
```bash
sudo nano /etc/dphys-swapfile
```
Adjust the swap size as needed
```conf
# Anywhere in file
CONF_SWAPSIZE=2048
```
```bash
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Enabling SPI
```bash
sudo nano /boot/config.txt
```
```
# Anywhere in file
dtparam=spi=on
dtoverlay=spi1-3cs
#1cs, 2cs for other amounts of chip select pins
```
And, reboot
## Test SPI
```bash
wget https://raw.githubusercontent.com/raspberrypi/linux/rpi-3.10.y/Documentation/spi/spidev_test.c
gcc -o spidev_test spidev_test.c
```
Wire SPI MISO and MOSI pins together
```bash
sudo ./spidev_test -D /dev/spidev0.0
```
Expected output
```
FF FF FF FF FF FF
40 00 00 00 00 95
FF FF FF FF FF FF
FF FF FF FF FF FF
FF FF FF FF FF FF
DE AD BE EF BA AD
F0 0D
```
## Setting Up Python
Python comes installed on Raspbian
```bash
pip install RPi.GPIO
```
Install [SPI-Py](https://github.com/lthiery/SPI-Py)
```bash
git clone https://github.com/lthiery/SPI-Py
cd SPI-Py
sudo python setup.py install
```
## Install Node.js
Search [Node.js unofficial builds](https://unofficial-builds.nodejs.org/download/release/) for an ARM-61 build of Node.js

Adjust URL as needed
```bash
wget https://unofficial-builds.nodejs.org/download/release/v20.4.0/node-v20.4.0-linux-armv6l.tar.xz
tar -xJf node-v20.4.0-linux-armv6l.tar.xz
sudo cp -R node-v20.4.0-linux-armv6l/* /usr/local/
```
Do not install npx, it is included already
```bash
npm i -g react
```
Need to increase Node heap space to install `npm` packages
```bash
sudo nano ~/.bashrc
```
```bash
# At end of file
export NODE_OPTIONS=--max-old-space-size=2048
```
Move to a new terminal session
```bash
# ONLY USE IF MAKING A NEW WEB SERVER (not cloning this repo)
# Takes a long time (800 sec) for me
npx create-react-app lightbar
cd lightbar
npm i sass
npm install @types/react @types/react-dom
```
Need to allow port `80` and `3000` for React deployment and testing
```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I OUTPUT -p tcp --sport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 3000 -j ACCEPT
sudo iptables -I OUTPUT -p tcp --sport 3000 -j ACCEPT
sudo netfilter-persistent save
```

## Setting Git User Details
For if you want to author commits
```bash
git config --global user.name "USERNAME"
git config --global user.email "EMAIL"
```
