#!/bin/bash

echo "->Disable network-manager"
sudo service network-manager stop
sleep 1

echo "->Setup hwsim interfaces"
#cleanup
sudo modprobe -r mac80211_hwsim
sudo modprobe mac80211_hwsim radios=1
sleep 1
sudo ifconfig hwsim0 up
sleep 1

echo "->Start hostapd on wlan1"
sleep 1
sudo killall hostapd
sleep 1
sudo hostapd hostapd.conf & 