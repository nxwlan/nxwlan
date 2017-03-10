# NxWLAN: Neighborhood eXtensible WLAN

## 1. What is NxWLAN?
The increased usage of IEEE 802.11 Wireless LAN (WLAN) in residential environments by unexperienced users leads to dense, unplanned and chaotic residential WLAN deployments.  Often WLAN Access Points (APs) are deployed unprofitable in terms of radio coverage and interference conditions. In many cases the usage of the neighbor’s AP would be beneficial as it would provide better radio coverage in some parts of the residential user’s apartment.  Moreover, the network performance can be dramatically improved by balancing the network load over spatially co-located APs. We address this problem by presenting Neighborhood extensibleWLAN (NxWLAN) which enables the secure extension of user’s home WLANs through usage of neighboring APs in residential environments with zero configuration efforts and without revealing WPA2 encryption keys to untrusted neighbor APs. NxWLAN makes use of virtualization techniques utilizing neighboring AP by deploying on-demand a Wireless Termination Point (WTP) on the neighboring AP and by tunneling encrypted 802.11 traffic to the Virtual Access Point (VAP) residing on the home AP. This allows the client devices to always authenticate against the home AP using the WPA2-PSK passphrase already stored in the device without any additional registration process. We implemented NxWLAN prototypically using off-the-shelf hardware and open source software. As the OpenFlow is not suited for forwarding native 802.11 frames, we built software switch using P4 language.  The performance evaluation in a small 802.11 indoor testbed showed the feasibility of our approach. NxWLAN is provided to the community as open source.

## 2. Contact
* Piotr Gawlowicz, TU-Berlin, gawlowicz@tkn
* Sven Zehl, TU-Berlin, zehl@tkn
* Anatolij Zubow, TU-Berlin, zubow@tkn
* tkn = tkn.tu-berlin.de
