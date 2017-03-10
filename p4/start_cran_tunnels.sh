#for radio head 1
sudo modprobe l2tp_eth
sudo ip l2tp add tunnel tunnel_id 1000 peer_tunnel_id 1000 \
          local 192.168.200.174 remote 192.168.200.32 \
          encap udp udp_sport 5001 udp_dport 6001
sudo ip l2tp add session tunnel_id 1000 session_id 1000 \
          peer_session_id 1000
sudo ip link set l2tpeth0 up
sudo ip link set l2tpeth0 up mtu 1488


#for radio head 2
sudo ip l2tp add tunnel tunnel_id 2000 peer_tunnel_id 1000 \
          local 192.168.200.174 remote 192.168.200.25 \
          encap udp udp_sport 5002 udp_dport 6002
sudo ip l2tp add session tunnel_id 2000 session_id 1000 \
          peer_session_id 1000
sudo ip link set l2tpeth1 up
sudo ip link set l2tpeth0 up mtu 1488