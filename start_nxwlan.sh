#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied; usage: $0 <phy>"
    exit 0
fi

phy=$1

# cleanup
sudo modprobe -r mac80211_hwsim


for i in `seq 1000 1020`;
do
  sudo ip l2tp del tunnel tunnel_id ${i} 2>/dev/null
done
sudo modprobe -r l2tp_eth


for i in `seq 0 10`;
do
  sudo iw dev mon${i} del 2>/dev/null
  sudo iw dev wlan${i} del 2>/dev/null
  sudo iw dev wifi${i} del 2>/dev/null
  sudo iw dev ap${i} del 2>/dev/null
  sudo iw dev inject${i} del 2>/dev/null
  sudo iw dev vap${i} del 2>/dev/null
done

sudo killall -9 python
sudo rfkill unblock all 2>/dev/null

#Configuring AP
sleep 1
sudo killall -9 hostapd 2> /dev/null
sleep 1

#Starting VAP STUFF for Rate Control
#sudo iw phy ${phy} interface add vap0 type managed
#sleep 1
#if [ "$HOSTNAME" = "nuc3" ]; then 
#    sudo ./idiot-hostapd/hostapd-20131120/hostapd/hostapd framework/apps/configs/nuc3/hostapd-idiot.conf &
#    sleep 5
#    sudo ./idiot-hostapd/hostapd-20131120/hostapd/hostapd_cli -p /tmp/hostapd-idiot/ new_sta ec:1f:72:82:09:56
#    sleep 2
#fi


#Start monitor port for VAP
sudo iw phy ${phy} interface add inject0 type managed
sleep 2
sudo iwconfig inject0 txpower 16dBm
sudo iwconfig inject0 txpower 16
sleep 1
sudo ifconfig inject0 up
sleep 2
sudo dumpcap -i inject0 -I -c 1 2>/dev/null
#Start Home AP
sudo iw phy ${phy} interface add ap5 type managed
sleep 1
sudo ifconfig ap5 192.168.6.1 netmask 255.255.255.0
sudo iwconfig ap5 txpower 16dBm
sudo iwconfig ap5 txpower 16
sleep 1
sudo service network-manager stop 2>/dev/null
sleep 1
if [ "$HOSTNAME" = "nuc2" ]; then
    printf '%s\n' "Running on NUC3"
    sudo ./hostapd-20131120/hostapd/hostapd framework/apps/configs/nuc2/hostapd-nuc2-real.conf &
elif [ "$HOSTNAME" = "nuc3" ]; then
    printf '%s\n' "Running in NUC3"
    sudo ./hostapd-20131120/hostapd/hostapd framework/apps/configs/nuc3/hostapd-nuc3-real.conf &
else
    printf '%s\n' "Running on unknown host, using standard hostapd-ch40.conf"
    sudo ./hostapd-20131120/hostapd/hostapd hostapd-20131120/hostapd/hostapd-ch40.conf &
fi
sleep 5

#Starting ResFi Agent
cd framework/
sudo python resfi_loader.py
