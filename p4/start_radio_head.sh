#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied; usage: $0 <PHYNAME>"
    exit 0
fi

echo "->Disable network-manager"
sudo service network-manager stop
sleep 1

CRAN_MAC=02:00:00:00:00:00
PHYNAME=$1

echo "->Creating monitor interface mon0 for passive frame sniffing..."

# cleanup
sudo iw dev mon0 del 2>/dev/null
sudo iw dev mon1 del 2>/dev/null
sudo iw dev mon2 del 2>/dev/null
sudo iw dev mon3 del 2>/dev/null
sudo iw dev wlan0 del 2>/dev/null
sudo iw dev wlan1 del 2>/dev/null
sudo iw dev wlan2 del 2>/dev/null
sudo iw dev wlan3 del 2>/dev/null
sudo iw dev wlan4 del 2>/dev/null
sudo iw dev wlan5 del 2>/dev/null
sudo iw dev wlan6 del 2>/dev/null

sleep 1
sudo rfkill unblock all

sleep 1

sudo iw phy $PHYNAME interface add mon0 type managed

sleep 1

sudo ifconfig mon0 up

sleep 1

sudo dumpcap -i mon0 -I -c 1

sleep 1

sudo iwconfig mon0 channel 1

sleep 1
sudo iw phy $PHYNAME interface add wlan0 type managed
sleep 1
sudo ifconfig wlan0 down
sleep 1
sudo ifconfig wlan0 hw ether $CRAN_MAC
sleep 1
sudo ifconfig wlan0 up

#set BSSID for acks
sudo hostapd hostapd_rh.conf &
sleep 1
sudo killall hostapd