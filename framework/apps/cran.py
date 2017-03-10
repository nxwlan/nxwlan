"""
    Hello World message sender as example application 
    for the ResFi framework.

    Copyright (C) 2016 Piotr Gawlowicz, Sven Zehl, Anatolij Zubow, Michael Doering, Adam Wolisz

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    {zehl, zubow, wolisz, doering}@tkn.tu-berlin.de
"""

__author__ = 'gawlowicz, zehl, zubow, wolisz, doering'

import time
import subprocess
import socket
import netifaces as ni
from common.iface_mon import InterfaceMonitor
from common.resfi_api import AbstractResFiApp
import numpy as np
import threading
from collections import deque

#P4 SWITCH PATHS
BMV2_PATH = '/home/robat/workspace/bmv2'
P4C_BM_PATH = '/home/robat/workspace/p4c-bm'
P4_DEBUGGER = '/home/robat/workspace/bmv2/tools/p4dbg.py'
P4_SWITCH_PATH = '/home/robat/workspace/bmv2/targets/simple_switch/simple_switch'
P4_SWITCH_CLI = '/home/robat/workspace/bmv2/targets/simple_switch/sswitch_CLI'

P4_PROG = './apps/p4/home_p4.json'

class VapEntity(object):
    def __init__(self, manager, neighbor, vapId):
        self.vapId = vapId
        self.log = manager.log
        self.manager = manager
        self.neighbor = neighbor
        self.iface_name = None
        self.local_ip_address = None
        self.remote_ip_address = None
        self.local_tunnel_id = None
        self.remote_tunnel_id = None
        self.local_session_id = None
        self.remote_session_id = None
        self.sport = None
        self.dport = None     
        self.mtu = 1488
        self.p4_port_id = None

    def setup_local_tunnel(self):
        '''
        sudo ip l2tp add tunnel tunnel_id 2000 peer_tunnel_id 1000 \
            local 192.168.200.174 remote 192.168.200.25 encap udp udp_sport 5002 udp_dport 6002
        sudo ip l2tp add session tunnel_id 2000 session_id 1000 peer_session_id 1000
        sudo ip link set l2tpeth0 up mtu 1488
        '''
        self.log.info("Setup local part of tunnel")
        cmd = 'sudo ip l2tp add tunnel tunnel_id {} peer_tunnel_id {} local {} remote {} encap udp udp_sport {} udp_dport {}'.format(self.local_tunnel_id, 
               self.remote_tunnel_id, self.local_ip_address, self.remote_ip_address, self.sport, self.dport)
        self.manager.app.run_command(cmd)
        time.sleep(1)

        cmd = 'sudo ip l2tp add session tunnel_id {} session_id {} peer_session_id {}'.format(self.local_tunnel_id, 
               self.local_session_id, self.remote_session_id)
        self.manager.app.run_command(cmd)
        time.sleep(1)

        #get iface name
        ifaceName = None
        cmd = "sudo ip l2tp show session"
        output = self.manager.app.run_command(cmd)
        output = output.split('\n')

        k = iter(output)
        for line in k:
            if not line:
                continue
            if line.split()[0] != 'Session':
                continue

            [mySession, myTunnel] = [int(s) for s in line.split() if s.isdigit()]
            line1 = k.next()
            line2 = k.next()
            line3 = k.next()
            if mySession == self.local_session_id and myTunnel == self.local_tunnel_id:
                ifaceName = line2.split()[-1]

        self.iface_name = ifaceName

        self.log.info("Added tunnel interface with name : {}".format(ifaceName))

        cmd = 'sudo ip link set {} up mtu 1488'.format(ifaceName)
        self.manager.app.run_command(cmd)
        time.sleep(1)
        cmd = 'sudo ifconfig {} up'.format(ifaceName)
        self.manager.app.run_command(cmd)
        time.sleep(1)

        return ifaceName


class LocalVapEntity(VapEntity):
    def __init__(self, manager, neighbor, vapId):
        super(LocalVapEntity, self).__init__(manager, neighbor, vapId)

    def request_remote_vap_setup(self):
        self.log.info('Send local config to neighbor : {}'.format(self.neighbor))
        my_msg = {}
        my_msg['payload'] = {'msgType' : 'remote_vap_create_request',
                             'peer' : self.local_ip_address,
                             'local_tunnel_id' : self.local_tunnel_id,
                             'remote_tunnel_id' : self.remote_tunnel_id,
                             'local_ip_address' : self.local_ip_address,
                             'remote_ip_address' : self.remote_ip_address,
                             'sport' : self.sport,
                             'dport' : self.dport,
                             'local_session_id' : self.local_session_id,
                             'remote_session_id' : self.remote_session_id
                             }
        self.manager.app.sendToNeighbor(my_msg, self.neighbor)

    def start_forwarding_frames(self):
        self.log.info('start_forwarding_frames called')
        '''
        table_add table_switch_da send_to_port 1 ff:ff:ff:ff:ff:ff => 0 from tunnel to hwsim
        table_add table_switch_da send_to_port 0 ff:ff:ff:ff:ff:ff => 1 from hwsim to tunnel

        table_add table_switch_da send_to_port 1 34:13:e8:24:77:be => 0  from STA
        table_add table_switch_da send_to_port 0 02:00:00:00:00:00 => 1  from AP
        '''
        #hwsim to tunnel
        #entry = 'table_add table_switch_da send_to_port 0 ff:ff:ff:ff:ff:ff => {}'.format(self.p4_port_id)
        #self.manager.app.p4SwitchManager.add_entry_to_switch(entry)
        entry = 'table_add table_wire_ports send_to_port 0 => {}'.format(self.p4_port_id)
        self.manager.app.p4SwitchManager.add_entry_to_switch(entry)

        #from tunnel to hwsim
        #entry = 'table_add table_switch_da send_to_port {} ff:ff:ff:ff:ff:ff => 0'.format(self.p4_port_id)
        #self.manager.app.p4SwitchManager.add_entry_to_switch(entry)
        entry = 'table_add table_wire_ports send_to_port {} => 0'.format(self.p4_port_id)
        self.manager.app.p4SwitchManager.add_entry_to_switch(entry)

        #hwsim to tunnel
        #entry = 'table_add table_switch_da send_to_port 0 02:00:00:00:00:00 => {}'.format(self.p4_port_id)
        #self.manager.app.p4SwitchManager.add_entry_to_switch(entry)


    def add_sta_frames(self, staMac):
        #from STA (tunnel) to hwsim0
        entry = 'table_add table_switch_da send_to_port {} {} => 0'.format(self.p4_port_id, staMac)
        self.manager.app.p4SwitchManager.add_entry_to_switch(entry)


class RemoteVapEntity(VapEntity):
    def __init__(self, manager, neighbor, vapId):
        super(RemoteVapEntity, self).__init__(manager, neighbor, vapId)
        self.stupidHostapd = None #TODO implement it

    def sent_config_to_local_vap(self):
        self.log.info('Send-back local config to neighbor : {}'.format(self.neighbor))
        my_msg = {}
        my_msg['payload'] = {'msgType' : 'remote_vap_create_completed',
                             'peer' : self.local_ip_address,
                             'local_tunnel_id' : self.local_tunnel_id,
                             'remote_tunnel_id' : self.remote_tunnel_id,
                             'local_ip_address' : self.local_ip_address,
                             'remote_ip_address' : self.remote_ip_address,
                             'sport' : self.sport,
                             'dport' : self.dport,
                             'local_session_id' : self.local_session_id,
                             'remote_session_id' : self.remote_session_id
                             }
        self.manager.app.sendToNeighbor(my_msg, self.neighbor)

    def start_visiting_ap(self, phyName):
        print("start_visiting_ap called")
        self.manager.app.run_command('sudo service network-manager stop')
        time.sleep(1)
        self.manager.app.run_command('sudo iw dev vap0 del 2>/dev/null')
        time.sleep(1)
        self.manager.app.run_command('sudo rfkill unblock all')
        time.sleep(1)
        cmd = 'sudo iw phy {} interface add vap0 type managed'.format(phyName)
        self.manager.app.run_command(cmd)
        time.sleep(1)

        print("setup vap0 interface on phy {}".format(phyName))

        #start fake hostapd on vap0, to set BSSID for acking
        #p = subprocess.Popen(["sudo", "hostapd", "./apps/configs/hostapd_vap.conf"])
        #time.sleep(1)
        #p.terminate()
        #p.wait()

        #run idiot hostapd for rate control and acking
        idiot_hostpad_path = "../idiot-hostapd/hostapd-20131120/hostapd/hostapd"
        idiot_hostpad_cli_command = "../idiot-hostapd/hostapd-20131120/hostapd/sta_adder.sh"
        # -p /tmp/hostapd-idiot/ new_sta ec:1f:72:82:09:56;"
        hostname = socket.gethostname()
        config_path = "./apps/configs/{}/hostapd-idiot.conf".format(hostname)
        p = subprocess.Popen(["sudo", idiot_hostpad_path, config_path])
        fake = subprocess.Popen(["sudo", idiot_hostpad_cli_command])

    def fake_sta_registration(self, cmd):
        pass

    def start_forwarding_frames(self):
        '''
        table_add table_switch_da send_to_port 1 ff:ff:ff:ff:ff:ff => 0
        table_add table_switch_da send_to_port 0 ff:ff:ff:ff:ff:ff => 1

        table_add table_switch_da send_to_port 1 34:13:e8:24:77:be => 0
        table_add table_switch_da send_to_port 0 02:00:00:00:00:00 => 1
        '''
        #from tunnel to inject/monitor iface
        #entry = 'table_add table_switch_da send_to_port {} ff:ff:ff:ff:ff:ff => 1'.format(self.p4_port_id)
        #self.manager.app.p4SwitchManager.add_entry_to_switch(entry)
        entry = 'table_add table_wire_ports send_to_port {} => 1'.format(self.p4_port_id)
        self.manager.app.p4SwitchManager.add_entry_to_switch(entry)

        #from monitor/inject iface to tunnel
        #entry = 'table_add table_switch_da send_to_port 1 ff:ff:ff:ff:ff:ff => {}'.format(self.p4_port_id)
        #self.manager.app.p4SwitchManager.add_entry_to_switch(entry)
        entry = 'table_add table_wire_ports send_to_port 1 => {}'.format(self.p4_port_id)
        self.manager.app.p4SwitchManager.add_entry_to_switch(entry)        

        #from tunnel to inject/monitor iface
        #entry = 'table_add table_switch_da send_to_port {} 02:00:00:00:00:00 => 1'.format(self.p4_port_id)
        #self.manager.app.p4SwitchManager.add_entry_to_switch(entry)


    def add_sta_frames(self, staMac):
        #from STA (monitor/inject) to tunnel
        entry = 'table_add table_switch_da send_to_port 1 {} => {}'.format(staMac, self.p4_port_id)
        self.manager.app.p4SwitchManager.add_entry_to_switch(entry)


class VapManager(object):
    def __init__(self, app):
        self.app = app
        self.log = app.log
        self.local_vaps = []
        self.remote_vaps = []
        self.vap_id_generator = 0
        self.tunnel_id_generator = 1000
        self.session_id_generator = 1000
        self.port_generator = 5001

        self.app.run_command('sudo modprobe l2tp_eth')

    def print_local_vaps(self):
        if len(self.local_vaps) == 0:
            return

        self.log.info("List of Local VAPs".format())
        for vap in self.local_vaps:
            self.log.info("\tID: {} Neighbor: {}".format(vap.vapId, vap.neighbor))

    def print_remote_vaps(self):
        if len(self.remote_vaps) == 0:
            return

        self.log.info("List of Remote VAPs".format())
        for vap in self.remote_vaps:
            self.log.info("\tID: {} Neighbor: {}".format(vap.vapId, vap.neighbor))

    def generate_vap_id(self):
        tmp = self.vap_id_generator
        self.vap_id_generator = self.vap_id_generator + 1
        return tmp

    def generate_tunnel_id(self):
        tmp = self.tunnel_id_generator
        self.tunnel_id_generator = self.tunnel_id_generator + 1
        return tmp

    def generate_session_id(self):
        tmp = self.session_id_generator
        self.session_id_generator = self.session_id_generator + 1
        return tmp

    def generate_port(self):
        tmp = self.port_generator
        self.port_generator = self.port_generator + 1
        return tmp

    def get_local_vap_by_neighbor(self, neighbor):
        for vap in self.local_vaps:
            if vap.neighbor == neighbor:
                return vap
        return None

    def get_remote_vap_by_neighbor(self, neighbor):
        for vap in self.remote_vaps:
            if vap.neighbor == neighbor:
                return vap
        return None

    def initialize_local_vap(self, neighbor):
        #check if vap is present
        vap = self.get_local_vap_by_neighbor(neighbor)
        if vap:
            return
        #otherwise, add new one
        self.log.info('Create new VAP for neighbor : {}'.format(neighbor))
        
        vapId = self.generate_vap_id()
        newVap = LocalVapEntity(self, neighbor, vapId)
        #newVap.iface_name = ''.join(['l2tpeth', str(vapId)])

        #local part            
        newVap.local_ip_address = self.app.hostname
        newVap.local_tunnel_id = self.generate_tunnel_id()
        newVap.local_session_id = self.generate_session_id()
        newVap.sport = self.generate_port()

        #remote part
        newVap.remote_ip_address = neighbor
        newVap.remote_tunnel_id = None
        newVap.remote_session_id = None
        newVap.dport = None

        self.local_vaps.append(newVap)

        #send local part of config to remote peer
        newVap.request_remote_vap_setup()
        return newVap
        
    def create_remote_vap(self, config):
        neighbor = str(config['peer'])
        vap = self.get_remote_vap_by_neighbor(neighbor)
        self.log.info('Received WTP creation request from neighbor : {}'.format(neighbor)) 
        if vap:
            return

        #generate local part of config
        vapId = self.generate_vap_id()
        newVap = RemoteVapEntity(self, neighbor, vapId)
        #newVap.iface_name = ''.join(['l2tpeth', str(vapId)])

        self.log.info('Create new WTP for neighbor : {}'.format(neighbor))
        #local part            
        newVap.local_ip_address = self.app.hostname
        newVap.local_tunnel_id = self.generate_tunnel_id()
        newVap.local_session_id = self.generate_session_id()
        newVap.sport = self.generate_port()

        #fill remote part from received config
        newVap.remote_ip_address = neighbor
        newVap.remote_tunnel_id = str(config['local_tunnel_id'])
        newVap.remote_session_id = str(config['local_session_id'])
        newVap.dport = str(config['sport'])

        self.remote_vaps.append(newVap)

        #send local part of config to remote peer
        newVap.sent_config_to_local_vap()

        #setup local part of tunnel iface
        newVap.iface_name = newVap.setup_local_tunnel()

        #add tunnel iface to p4 and save portID
        p4SwithManager = self.app.p4SwitchManager
        newVap.p4_port_id = p4SwithManager.add_tunnel_port(newVap.iface_name)
        self.log.info("WTP - Added tunnel iface : {} into P4 switch with ID: {}".format(newVap.iface_name, newVap.p4_port_id))

        newVap.start_forwarding_frames()

        newVap.start_visiting_ap("phy0")

    def complete_local_vap(self, config):
        neighbor = str(config['peer'])
        vap = self.get_local_vap_by_neighbor(neighbor)
        if not vap:
            return
        
        self.log.info('Complete VAP setup for neighbor : {}'.format(neighbor))
        #fill remote part from received config
        vap.remote_ip_address = neighbor
        vap.remote_tunnel_id = str(config['local_tunnel_id'])
        vap.remote_session_id = str(config['local_session_id'])
        vap.dport = str(config['sport'])

        #setup local part of tunnel iface
        vap.iface_name = vap.setup_local_tunnel()

        #add tunnel iface to p4 and save portID
        p4SwithManager = self.app.p4SwitchManager
        vap.p4_port_id = p4SwithManager.add_tunnel_port(vap.iface_name)
        self.log.info("VAP - Added tunnel iface : {} into P4 switch with ID: {}".format(vap.iface_name, vap.p4_port_id))

        vap.start_forwarding_frames()

    def remove_vap(self, neighbor):
        #check if vap is present and remove
        vap = self.get_local_vap_by_neighbor(neighbor)
        if vap:
            self.log.info('Delete VAP for neighbor : {}'.format(neighbor))
            self.local_vaps.remove(vap)


class P4SwitchManager(object):
    def __init__(self, app):
        self.app = app
        self.log = app.log
        self.port_id_generator = 0
        self.start_p4_switch()

    def generate_port_id(self):
        tmp = self.port_id_generator
        self.port_id_generator = self.port_id_generator + 1
        return tmp

    def start_p4_switch(self):
        self.p4_switch_proc = subprocess.Popen(["sudo", P4_SWITCH_PATH, P4_PROG, '--debugger'])
        time.sleep(1)

        #entry = 'table_set_default table_switch_da _drop'
        #self.add_entry_to_switch(entry)

        entry = 'table_set_default table_wire_ports _drop'
        self.add_entry_to_switch(entry)

        entry = 'table_set_default table_modify_ethernet_header _drop'
        self.add_entry_to_switch(entry)

        entry = 'table_set_default table_drop_tx_frames_from_monitor _nop'
        self.add_entry_to_switch(entry)

        entry = 'table_add table_drop_tx_frames_from_monitor _drop 1 0x0 =>'
        self.add_entry_to_switch(entry)

        entry = 'table_set_default table_drop_rx_beacons _nop'
        self.add_entry_to_switch(entry)

        entry = 'table_add table_drop_rx_beacons _drop 1 0x0 0x8 =>'
        self.add_entry_to_switch(entry)

        entry = 'table_set_default table_drop_control_frames _nop'
        self.add_entry_to_switch(entry)

        entry = 'table_add table_drop_control_frames _drop 0x1 =>'
        self.add_entry_to_switch(entry)


    def add_entry_to_switch(self, entry):
        cmd = "echo \"{}\" | {}".format(entry, P4_SWITCH_CLI)
        return self.app.run_command(cmd)

    def add_port(self, ifaceName):
        portId = self.generate_port_id()
        entry = 'port_add {} {}'.format(ifaceName, portId)
        self.add_entry_to_switch(entry)
        return portId

    def add_radio_tap_port(self, ifaceName):
        portId = self.add_port(ifaceName)
        entry = 'table_add table_modify_ethernet_header remove_eth_header {} =>'.format(portId)
        self.add_entry_to_switch(entry)
        return portId

    def add_tunnel_port(self, ifaceName):
        portId = self.add_port(ifaceName)
        entry = 'table_add table_modify_ethernet_header add_eth_header {} =>'.format(portId)
        self.add_entry_to_switch(entry)
        return portId



"""
    helper to calculate moving average
"""
class RunningMeanCalculator():
    def __init__(self):
        pass

    def running_mean(self, x, N):
        cumsum = np.cumsum(np.insert(x, 0, 0))
        return (cumsum[N:] - cumsum[:-N]) / N

"""
    Estimates the wireless MAC layer bitrate of a client within a cell
"""
class WifiCapacityEstimator():
    def __init__(self, log, max_mac_rate):
        self.max_mac_rate = max_mac_rate
        self.log = log
    def calc(self, per_client_phy_rate, av_backhaul):
        """
        The slowest clients data rate represents an upper boundary of every clients long term throughput.
        """
        
        # dirty shit        
        #for i in range(len(per_client_phy_rate)-1):
        #    per_client_phy_rate[i] = 6.0

        mac_rate = 0.0
        for r_phy in per_client_phy_rate:
            #print "R_PHY: "+ str(r_phy)
            self.log.info("R:PHY; {}".format(str(r_phy)))
            #mac_rate = 54.0
            mac_rate = mac_rate + (1.0 / r_phy)

        nac_rate = 1.0 / mac_rate
        self.log.info("MAC Rate (Wifi Only): {}".format(str(nac_rate)))

        # take minimum of available capacity of wireless and backhaul
        nac_rate = min(nac_rate, av_backhaul/1e6)
        self.log.info("MAC Rate (WiFi + Backhaul):{} ".format(str(nac_rate)))
        return nac_rate

    def get_normalized(self, per_client_phy_rate, av_backhaul):
        return min(1.0, self.calc(per_client_phy_rate, av_backhaul) / float(self.max_mac_rate))


"""
    Estimates the transmit power to be used for probe reply packets based on selected priority
"""
class ProbeReplyTxPowerCtrl():
    def __init__(self, log, max_tx_power_dbm, default_tx_power_dbm, low_p_rx_dbm = -90, high_p_rx_dbm = -50):
        self.max_tx_power_dbm = max_tx_power_dbm
        self.default_tx_power_dbm = default_tx_power_dbm
        self.low_p_rx_dbm = low_p_rx_dbm
        self.high_p_rx_dbm = high_p_rx_dbm
        self.delta_p_rx_dbm = high_p_rx_dbm - low_p_rx_dbm
        self.log = log
    def calc_tx_power(self, p_rx_dbm, prio):
        pl_db = self.default_tx_power_dbm - p_rx_dbm

        #print "pl_db: ", pl_db
        self.log.info("pl_db: {}".format(str(pl_db)))
        """
        (1) Scale power
        """
        tx_power_dbm_low = max(1, self.default_tx_power_dbm - (p_rx_dbm - self.low_p_rx_dbm))

        #print "tx_power_dbm_low: ", tx_power_dbm_low
        self.log.info("tx_power_dbm_low: {}".format(str(tx_power_dbm_low)))
        tx_power_dbm_adapted = min(self.max_tx_power_dbm, tx_power_dbm_low + prio * self.delta_p_rx_dbm)

        assert(tx_power_dbm_adapted >= 0)
        assert(tx_power_dbm_adapted <= self.max_tx_power_dbm)
        self.log.info("tx_power_dbm_final:  {}".format(str(tx_power_dbm_adapted)))
        #print "tx_power_dbm_final: ", tx_power_dbm_adapted

        p_rx_dbm_after = tx_power_dbm_adapted - pl_db
        self.log.info("p_rx_dbm_after:  {}".format(str(p_rx_dbm_after)))
        #print "=== p_rx_dbm_after: ", p_rx_dbm_after
        #assert (p_rx_dbm_after >= self.low_p_rx_dbm)

        return tx_power_dbm_adapted

"""
    Estimates the expected PHY bitrate from the received signal strength (probe request)
"""
class PhyDataRateCalculator():
    def __init__(self):

        """
            Using table:
            11-03-0845-01-000n-11-03-0845-00-000n-receiver-sensitivity-tables-mimo-ofdm.ppt
            slide 10

            note: atheros chip noise floor: -95 dBm
        """
        # using emperical values

        self.data_rate_sensitivity_tbl = {}
        self.data_rate_sensitivity_tbl[6] = -86 #-83.9
        self.data_rate_sensitivity_tbl[9] = -84 #-79.8
        self.data_rate_sensitivity_tbl[12] = -82 #-81.1
        self.data_rate_sensitivity_tbl[18] = -80 #-76.5
        self.data_rate_sensitivity_tbl[24] = -77 #-75.5
        self.data_rate_sensitivity_tbl[36] = -74 #-70.6
        self.data_rate_sensitivity_tbl[48] = -72 #-67.9
        self.data_rate_sensitivity_tbl[54] = -70 #-65.8

    def get_phy_bitrate(self, rx_signal):
        best_rate = 1

        for key, value in self.data_rate_sensitivity_tbl.iteritems():
            if value <= rx_signal:
                if best_rate < key:
                    best_rate = key

        return best_rate

"""
    Main class: calculates the transmit power for probe reply taking into account the expected signal quality and the
    available capacity within the WiFi cell (AP).
"""
class ReadinessToServe(threading.Thread):

    def __init__(self, app):
        threading.Thread.__init__(self)
        self.app = app
        self.log = app.log
        self.MOV_AVG_WND = 5 # in seconds
        self.tbl = {}
        self.sample_interval = 1
        self.min_client_avg_tx_rate_mbps = 0 # clients mit tx bitrate of min 1 Mbps are treated as fat clients -> we will compete with them for medium

        self.max_mac_rate_mbps = 35.0 # max mac layer throughput of single link in 802.11a using 54 Mbps phyrate
        self.capacity_est = WifiCapacityEstimator(app.log, self.max_mac_rate_mbps)

        self.pc = PhyDataRateCalculator()

        self.max_tx_power_dbm = 16 # dBm
        self.default_tx_power_dbm = 16 #CISCO Stick fix power; old: self.max_tx_power_dbm # dBm
        self.low_p_rx_dbm = -90 #dBm
        self.high_p_rx_dbm = -50 #dBm
        self.p_ctrl = ProbeReplyTxPowerCtrl(self.log, self.max_tx_power_dbm, self.default_tx_power_dbm, self.low_p_rx_dbm, self.high_p_rx_dbm)
        self.infoAvBackhaulMap = {}

    def calculate_preply_tx_power(self, new_client_preq_rx_dbm):
        """
        Call this function for each Probe request received from a client station.
        :param new_client_preq_rx_dbm: the received power of the probe request
        :return: the tx power to be used for probe reply for the HAP and all neighboring VAPs
        """

        all_probe_reply_tx_power_dbm_adapted = {}

        """
        Estimate the clients having medium/large traffic
        """
        phy_rate_tbl = []
        for client_addr in self.tbl:
            # calc mac layer transmit rate
            v = list(self.tbl[client_addr])

            mac_thr_values = []
            for ii in range(len(v)-1):
                mac_thr_values.append( (v[ii+1] - v[ii]) / self.sample_interval )
            #Sven hack, check if this makes sense....
            if len(mac_thr_values) <= 0:
                continue
            #hehe
            mac_txrate_avg = (sum(mac_thr_values) / len(mac_thr_values)) / 1e6

            # filter small flows
            if mac_txrate_avg >= self.min_client_avg_tx_rate_mbps:
                # take the PHY bitrate
                print "!!! JO : Client Addr: "+str(client_addr)
                cl_phy_rate = self.app.getTxBitrateStation(client_addr)
                phy_rate_tbl.append(cl_phy_rate)

        """
        Predict the expected phy rate of new client towards this AP using the received signal measured from probe request
        """
        new_client_phy_rate = self.pc.get_phy_bitrate(new_client_preq_rx_dbm)
        self.log.info("new_client_phy_rate: {}".format(str(new_client_phy_rate))) 
        #print "new_client_phy_rate:", new_client_phy_rate

        """
        Consider the available backhaul capacity for this node as well as all neighboring APs which can be used as VAP
        """
        #my_av_dl = self.app.ifaceMon.get_avaiable_dl()
        #my_av_ul = self.app.ifaceMon.get_avaiable_ul()
        my_av_dl = 50.0*1e6
        my_av_ul = 50.0*1e6

        #This is hack
        if not my_av_dl:
            my_av_dl = 1e9
            my_av_ul = 1e9
        self.log.info("my_av_ul: {} my_av_dkl: {}".format(str(my_av_ul), str(my_av_dl)))
        #print "my_av_ul: "+str(my_av_ul)
        #print "my_av_dl: "+str(my_av_dl)
        #if not my_av_dl or not my_av_ul:
            #print "Have to wait, currently no measurments available..."
            #my_av_dl = 0
            #my_av_ul = 0

        """
        Predict the expected MAC bitrate in the cell by considering multiple access in cell; normalize it in order to calculate priority
        """
        phy_rate_tbl.append(new_client_phy_rate)
        if self.app.hostname == "XXXXXXXX":
            print "IAM THE ASSHOLE!"
            new_client_mac_rate_norm = self.capacity_est.get_normalized(phy_rate_tbl, 1e3)
        else:
            new_client_mac_rate_norm = self.capacity_est.get_normalized(phy_rate_tbl, my_av_dl)
        self.log.info("new_client_mac_rate_norm: {}".format(str(new_client_mac_rate_norm)))
        #print "new_client_mac_rate_norm: ", new_client_mac_rate_norm
         
        """
        Calculate the transmit power of the probe reply while considering the priority
        """
        probe_reply_tx_power_dbm_adapted = self.p_ctrl.calc_tx_power(new_client_preq_rx_dbm, new_client_mac_rate_norm)
        self.log.info("probe_reply_tx_power_dbm_adapted: {}".format(str(probe_reply_tx_power_dbm_adapted)))
        #print "probe_reply_tx_power_dbm_adapted:", probe_reply_tx_power_dbm_adapted

        all_probe_reply_tx_power_dbm_adapted[self.app.hostname] = probe_reply_tx_power_dbm_adapted

        # for each neighbor
        for nb in self.infoAvBackhaulMap:
            #nb_av_dl = self.infoAvBackhaulMap[nb]['av_dl_backhaul']
            #nb_av_ul = self.infoAvBackhaulMap[nb]['av_ul_backhaul']
            nb_av_dl = 50.0*1e6
            nb_av_ul = 50.0*1e6

            #print "nb_av_dl: "+str(nb_av_dl)
            #print "nb_av_ul: "+str(nb_av_ul)
            self.log.info("nb_av_ul: {}, nb_av_dl: {}".format(str(nb_av_ul), str(nb_av_dl)))
            bottleneck_rate = min(min(nb_av_dl, nb_av_ul), my_av_dl)

            """
            Predict the expected MAC bitrate in the cell by considering multiple access in cell; normalize it in order to calculate priority
            """
            #phy_rate_tbl.append(new_client_phy_rate)
            new_client_mac_rate_norm = self.capacity_est.get_normalized(phy_rate_tbl, bottleneck_rate)
            self.log.info("new_client_mac_rate_norm: {}".format(str(new_client_mac_rate_norm)))
            #print "new_client_mac_rate_norm: ", new_client_mac_rate_norm

            """
            Calculate the transmit power of the probe reply while considering the priority
            """
            probe_reply_tx_power_dbm_adapted = self.p_ctrl.calc_tx_power(new_client_preq_rx_dbm, new_client_mac_rate_norm)
            self.log.info("probe_reply_tx_power_dbm_adapted: {}".format(str(probe_reply_tx_power_dbm_adapted)))
            #print "probe_reply_tx_power_dbm_adapted:", probe_reply_tx_power_dbm_adapted

            all_probe_reply_tx_power_dbm_adapted[nb] = probe_reply_tx_power_dbm_adapted

        return all_probe_reply_tx_power_dbm_adapted

    def run(self):
        while True:
            """
            Collect statistics about transmitted bytes to each served client station used for fat client detection
            """
            #self.tbl = {}
            # update table of served clients
            client_addrs = self.app.getMacAddrAssociatedClients()
            for client_addr in client_addrs:
                if client_addr not in self.tbl:
                    self.tbl[client_addr] = deque([], self.MOV_AVG_WND)

            # update tx bytes
            for client_addr in client_addrs:
                cl_tx_bytes = self.app.getMACTxBytesStation(client_addr)
                if cl_tx_bytes is not None:
                    self.tbl[client_addr].append(cl_tx_bytes * 8)
                else:
                    del self.tbl[client_addr]
            time.sleep(self.sample_interval)



class ResFiApp(AbstractResFiApp):
    def __init__(self, log, agent):
        AbstractResFiApp.__init__(self, log, "de.berlin.tu.tkn.cran", agent)
        self.hostname = self.getHostname('eth0')
        self.ifaceMon = InterfaceMonitor(iface='eth0', interval=1, window=10)
        self.ifaceMon.setDaemon(True)
        self.homeAP_hostapd_proc = None
        self.p4_switch_proc = None
        self.vapManager = VapManager(self)
        self.p4SwitchManager = None
        self.started = False
        self.startTime = None
        self.rts_algo = ReadinessToServe(self)

        if not hasattr(self, 'msgQueue'):
            self.msgQueue = []

    def getHostname(self, iface):
        hostname = ni.ifaddresses(iface)[2][0]['addr']
        return hostname

    def name_for_mac(self, mac):
        for i in ni.interfaces():
            addrs = ni.ifaddresses(i)
            if_mac = addrs[ni.AF_LINK][0]['addr']
            if if_mac == mac:
                return i
        return None

    def run_command(self, command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        result = p.communicate()[0]
        return result

    #Input dbm
    def set_proberesponse_TXPWR(self, homepwr, neighborpwr):
        #calculate dbm to atheros register:
        # 0 -> max power
        # 1 -> 0.5 dBm
        # 2 -> 1 dBm
        # etc...
        # max value = 100, but limited by max tx power set by user e.g. via iwconfig
        homepwr_ath = int(homepwr * 2)
        neighborpwr_ath = int(neighborpwr *2)
        #print "Setting Probe Response PWR to "+str(homepwr)+" (home AP) and "+str(neighborpwr)+ " (neighbor AP)"
        commandHome = 'sudo bash -c \'echo \"10002 '+str(homepwr_ath)+' 0\" > /sys/kernel/debug/ieee80211/phy0/ath9k/per_flow_tx_power\''
        commandNeighbor = 'sudo bash -c \'echo \"10001 '+str(neighborpwr_ath)+' 0\" > /sys/kernel/debug/ieee80211/phy0/ath9k/per_flow_tx_power\''
        self.run_command(commandHome)
        self.run_command(commandNeighbor)

    def start_home_ap(self):
        self.log.debug('setup hwsim')
        self.run_command('sudo modprobe -r mac80211_hwsim')
        time.sleep(1)
        self.run_command('sudo modprobe mac80211_hwsim radios=1')
        time.sleep(1)
        self.run_command('sudo ifconfig hwsim0 up')
        time.sleep(1)

        iface_name = self.name_for_mac("02:00:00:00:00:00")
        self.log.info("Name of HOME_AP iface: {}".format(iface_name))

        self.run_command('sudo service network-manager stop')
        self.log.debug("Start hostapd on : {}".format(iface_name))
        hostname = socket.gethostname()
        path = "./apps/configs/" + hostname + "/hostapd_hwsim.conf"
        self.homeAP_hostapd_proc = subprocess.Popen(["sudo", "hostapd", path])

    def stop_home_ap(self):
        self.homeAP_hostapd_proc.terminate()
        returncode = self.homeAP_hostapd_proc.wait()

        self.log.debug('remove hwsim')
        self.run_command('sudo modprobe -r mac80211_hwsim')

    def start_mon_iface(self, phyName, ifaceName):
        #already started in bash script
        time.sleep(1)
        self.run_command('sudo ifconfig {} up'.format(ifaceName))
        time.sleep(1)
        return 

    """
    Function will be started by ResFi runtime
    """
    def run(self):
        self.startTime = time.time()
        self.log.debug("%s: plugin::hello-world started ... " % self.agent.getNodeID())

        # wait until DL and UL are measured
        self.ifaceMon.start()

        # start P4 switch
        self.p4SwitchManager = P4SwitchManager(self)

        # start Home AP on hwsim
        self.start_home_ap()
        self.log.info("Add hwsim0 port to P4 switch")
        self.p4SwitchManager.add_radio_tap_port("hwsim0")

        # start monitor iface for frames injection
        self.log.info("Add monitor port to P4 switch")
        self.start_mon_iface("phy0", "inject0")
        self.p4SwitchManager.add_radio_tap_port("inject0")

        # start Wifi stuff
        self.rts_algo.daemon = True
        self.rts_algo.start()

        ##while not self.ifaceMon.connectionMeasured:
        ##    time.sleep(1)

        time.sleep(30)
        # setup local part of VAP and send setup request to all one-hop neighbors
        neighbors = self.getNeighbors()
        for neighbor in neighbors:
            self.vapManager.initialize_local_vap(neighbor)

        self.log.info("!!! VAP APP STARTED !!!")
        self.started = True

        # process already received msgs
        for msg in self.msgQueue:
            self.process_msg(msg)

        # control loop
        while not self.isTerminated():
            self.log.debug("Notify my neighbors about my current available backhaul capacity")
            av_dl = self.ifaceMon.get_avaiable_dl()
            av_ul = self.ifaceMon.get_avaiable_ul()
            av_dl = 30.0 *1e6
            av_ul = 30.0 *1e6
            if av_dl and av_ul:
                my_msg = {}
                my_msg['payload'] = {'msgType' : 'av_backhaul_announcement', 'hostname' : self.hostname, 'av_dl_backhaul' : av_dl, 'av_ul_backhaul' : av_ul}
                self.sendToNeighbors(my_msg, 1)
            time.sleep(1) 

        self.log.debug("%s: plugin::VAP stopped ... " % self.agent.getNodeID())
        self.stop_home_ap()


    def process_msg(self, json_data):
        msgPayload = json_data['payload']
        msgType = msgPayload['msgType']
        self.log.debug("Received MSG of MsgType: {}".format(msgType))

        if msgType == "remote_vap_create_request":
            self.vapManager.create_remote_vap(msgPayload)
        elif msgType == "remote_vap_create_completed":
            self.vapManager.complete_local_vap(msgPayload)
        elif msgType == "av_backhaul_announcement":
            # update by knowledge

            #timestampSent = json_data['tx_time_mus']
            #sender = json_data['originator']
            av_dl_backhaul = float(msgPayload['av_dl_backhaul'])
            av_ul_backhaul = float(msgPayload['av_ul_backhaul'])
            hostname = msgPayload['hostname']

            # save last update of each node
            self.rts_algo.infoAvBackhaulMap[hostname] = {'av_dl_backhaul': av_dl_backhaul, 'av_ul_backhaul': av_ul_backhaul}
        else:
            self.log.info("MsgType: {} not supported; Discard msg".format(msgType))
            pass


    """
    receive callback function
    """
    def rx_cb(self, json_data):
        #self.log.info("%s :: recv() msg from %s at %d: %s" % (self.ns, json_data['originator'], 
        #    json_data['tx_time_mus'], json_data))

        if not hasattr(self, 'started') or (hasattr(self, 'started') and not self.started):
            if not hasattr(self, 'msgQueue'):
                self.msgQueue = []
            self.msgQueue.append(json_data)
            return

        self.process_msg(json_data)


    """
    new Link Notification Callback
    """
    def newLink_cb(self, nodeID):
        self.log.info("%s ::newLink_cb() new AP neighbor detected notification (newLink: %s)" 
            % (self.ns, nodeID))
        time.sleep(10)
        self.vapManager.initialize_local_vap(nodeID)


    """
    Link Lost Notification Callback
    """
    def linkFailure_cb(self, nodeID):
        self.log.info("%s :: linkFailure_cb() neighbor AP disconnected (lostLink: %s)" 
            % (self.ns, nodeID))

        self.vapManager.remove_vap(nodeID)

    """
    Probe request received from client station callback
    """
    def probeReqRec_cb(self, payload, rssi):
        #self.log.info("%s ::probeReqRec() new Probe Request Received (rssi: %s), sender: %s"
        #    % (self.ns, str(rssi), str(payload[:12])))
        if "EC1F72820956" not in payload:
            return
        if not self.startTime or (time.time() - self.startTime) < 30.0:
            return 
        rssi = float(rssi)
        homepwr = 20.0
        neighborpwr = 20.0
        self.log.info("%s ::probeReqRec() new Probe Request Received (rssi: %s)"
            % (self.ns, str(rssi)))
        probe_reply_tx_power = self.rts_algo.calculate_preply_tx_power(rssi)
        if probe_reply_tx_power:
            for key in probe_reply_tx_power:
                if key == self.agent.getNodeID():
                    homepwr = probe_reply_tx_power[key]
                else:
                    neighborpwr = probe_reply_tx_power[key]
            self.log.info("homepwr: {} neighborpwr: {}".format(str(homepwr), str(neighborpwr)))
        self.set_proberesponse_TXPWR(homepwr, neighborpwr)
