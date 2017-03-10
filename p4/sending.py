sendp(RadioTap()/
          Dot11(addr1="ff:ff:ff:ff:ff:ff",addr2=RandMAC(),addr3=RandMAC())/
          Dot11Beacon(cap="ESS")/
          Dot11Elt(ID="SSID",info="test1234")/
          Dot11Elt(ID="Rates",info='\x82\x84\x0b\x16')/
          Dot11Elt(ID="DSset",info="\x01")/
          Dot11Elt(ID="TIM",info="\x00\x01\x00\x00"),iface="hwsim0",loop=1, inter=1)


sudo tcpdump -i mon0 -e not type mgt subtype beacon

from scapy.all import *

def pkt_callback(pkt):
     if pkt.addr2 == "02:00:00:00:00:00":
          sendp(pkt, iface="mon0",loop=0)

sniff(iface="hwsim0", prn=pkt_callback, store=0)




from scapy.all import *

def pkt_callback(pkt):
     if pkt.addr2 == "34:13:e8:24:77:be" or pkt.addr2 == None: 
          sendp(RadioTap()/pkt.payload, iface="hwsim0",loop=0)

sniff(iface="mon0", prn=pkt_callback, store=0)