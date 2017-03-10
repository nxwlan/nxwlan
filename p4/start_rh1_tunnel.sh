sudo modprobe l2tp_eth
sudo ip l2tp add tunnel tunnel_id 1000 peer_tunnel_id 1000 \
          local 192.168.200.32 remote 192.168.200.174 \
          encap udp udp_sport 6001 udp_dport 5001
sudo ip l2tp add session tunnel_id 1000 session_id 1000 \
          peer_session_id 1000
sudo ip link set l2tpeth0 up
sudo ip link set l2tpeth0 up mtu 1488