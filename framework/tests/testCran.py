from random import randint
import numpy as np
import threading
from collections import deque
import time
import subprocess
import socket
import logging

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
    def __init__(self, max_mac_rate):
        self.max_mac_rate = max_mac_rate

    def calc(self, per_client_phy_rate, av_backhaul):
        """
        The slowest clients data rate represents an upper boundary of every clients long term throughput.
        """

        mac_rate = 0.0
        for r_phy in per_client_phy_rate:
            mac_rate = mac_rate + (1.0 / r_phy)

        nac_rate = 1.0 / mac_rate

        # take minimum of available capacity of wireless and backhaul
        nac_rate = min(nac_rate, av_backhaul)

        return nac_rate

    def get_normalized(self, per_client_phy_rate, av_backhaul):
        return min(1.0, self.calc(per_client_phy_rate, av_backhaul) / float(self.max_mac_rate))


"""
    Estimates the transmit power to be used for probe reply packets based on selected priority
"""
class ProbeReplyTxPowerCtrl():
    def __init__(self, max_tx_power_dbm, default_tx_power_dbm, low_p_rx_dbm = -90, high_p_rx_dbm = -50):
        self.max_tx_power_dbm = max_tx_power_dbm
        self.default_tx_power_dbm = default_tx_power_dbm
        self.low_p_rx_dbm = low_p_rx_dbm
        self.high_p_rx_dbm = high_p_rx_dbm
        self.delta_p_rx_dbm = high_p_rx_dbm - low_p_rx_dbm

    def calc_tx_power(self, p_rx_dbm, prio):
        pl_db = self.default_tx_power_dbm - p_rx_dbm

        print "pl_db: ", pl_db

        """
        (1) Scale power
        """
        tx_power_dbm_low = max(0, self.default_tx_power_dbm - (p_rx_dbm - self.low_p_rx_dbm))

        print "tx_power_dbm_low: ", tx_power_dbm_low

        tx_power_dbm_adapted = min(self.max_tx_power_dbm, tx_power_dbm_low + prio * self.delta_p_rx_dbm)

        assert(tx_power_dbm_adapted >= 0)
        assert(tx_power_dbm_adapted <= self.max_tx_power_dbm)

        print "tx_power_dbm_final: ", tx_power_dbm_adapted

        p_rx_dbm_after = tx_power_dbm_adapted - pl_db

        print "=== p_rx_dbm_after: ", p_rx_dbm_after
        assert (p_rx_dbm_after >= self.low_p_rx_dbm)

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
        """
        self.data_rate_sensitivity_tbl = {}
        self.data_rate_sensitivity_tbl[6] = -83.9
        self.data_rate_sensitivity_tbl[9] = -79.8
        self.data_rate_sensitivity_tbl[12] = -81.1
        self.data_rate_sensitivity_tbl[18] = -76.5
        self.data_rate_sensitivity_tbl[24] = -75.5
        self.data_rate_sensitivity_tbl[36] = -70.6
        self.data_rate_sensitivity_tbl[48] = -67.9
        self.data_rate_sensitivity_tbl[54] = -65.8

    def get_phy_bitrate(self, rx_signal):
        best_rate = 0

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
        self.MOV_AVG_WND = 5 # in seconds
        self.tbl = {}
        self.sample_interval = 1
        self.min_client_avg_tx_rate_mbps = 1 # clients mit tx bitrate of min 1 Mbps are treated as fat clients -> we will compete with them for medium

        self.max_mac_rate_mbps = 35.0 # max mac layer throughput of single link in 802.11a using 54 Mbps phyrate
        self.capacity_est = WifiCapacityEstimator(self.max_mac_rate_mbps)

        self.pc = PhyDataRateCalculator()

        self.max_tx_power_dbm = 24 # dBm
        self.default_tx_power_dbm = self.max_tx_power_dbm # dBm
        self.low_p_rx_dbm = -90 #dBm
        self.high_p_rx_dbm = -50 #dBm
        self.p_ctrl = ProbeReplyTxPowerCtrl(self.max_tx_power_dbm, self.default_tx_power_dbm, self.low_p_rx_dbm, self.high_p_rx_dbm)
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

            mac_txrate_avg = (sum(mac_thr_values) / len(mac_thr_values)) / 1e6

            # filter small flows
            if mac_txrate_avg >= self.min_client_avg_tx_rate_mbps:
                # take the PHY bitrate
                cl_phy_rate = self.app.getTxBitrateStation(client_addr)

                phy_rate_tbl.append(cl_phy_rate)

        """
        Predict the expected phy rate of new client towards this AP using the received signal measured from probe request
        """
        new_client_phy_rate = self.pc.get_phy_bitrate(new_client_preq_rx_dbm)
        print "new_client_phy_rate:", new_client_phy_rate

        """
        Consider the available backhaul capacity for this node as well as all neighboring APs which can be used as VAP
        """
        my_av_dl = 5 #self.app.ifaceMon.get_avaiable_dl()
        my_av_ul = 3 #self.app.ifaceMon.get_avaiable_ul()

        """
        Predict the expected MAC bitrate in the cell by considering multiple access in cell; normalize it in order to calculate priority
        """
        phy_rate_tbl.append(new_client_phy_rate)
        new_client_mac_rate_norm = self.capacity_est.get_normalized(phy_rate_tbl, my_av_dl)
        print "new_client_mac_rate_norm: ", new_client_mac_rate_norm

        """
        Calculate the transmit power of the probe reply while considering the priority
        """
        probe_reply_tx_power_dbm_adapted = self.p_ctrl.calc_tx_power(new_client_preq_rx_dbm, new_client_mac_rate_norm)
        print "probe_reply_tx_power_dbm_adapted:", probe_reply_tx_power_dbm_adapted

        all_probe_reply_tx_power_dbm_adapted[self.app.hostname] = probe_reply_tx_power_dbm_adapted


        # for each neighbor
        for nb in self.infoAvBackhaulMap:
            nb_av_dl = self.infoAvBackhaulMap[nb]['av_dl_backhaul']
            nb_av_ul = self.infoAvBackhaulMap[nb]['av_ul_backhaul']

            bottleneck_rate = min(min(nb_av_dl, nb_av_ul), my_av_dl)

            """
            Predict the expected MAC bitrate in the cell by considering multiple access in cell; normalize it in order to calculate priority
            """
            phy_rate_tbl.append(new_client_phy_rate)
            new_client_mac_rate_norm = self.capacity_est.get_normalized(phy_rate_tbl, bottleneck_rate)
            print "new_client_mac_rate_norm: ", new_client_mac_rate_norm

            """
            Calculate the transmit power of the probe reply while considering the priority
            """
            probe_reply_tx_power_dbm_adapted = self.p_ctrl.calc_tx_power(new_client_preq_rx_dbm, new_client_mac_rate_norm)
            print "probe_reply_tx_power_dbm_adapted:", probe_reply_tx_power_dbm_adapted

            all_probe_reply_tx_power_dbm_adapted[nb] = probe_reply_tx_power_dbm_adapted

        return all_probe_reply_tx_power_dbm_adapted

    def run(self):
        while True:
            """
            Collect statistics about transmitted bytes to each served client station used for fat client detection
            """
            # update table of served clients
            client_addrs = self.app.getMacAddrAssociatedClients()
            for client_addr in client_addrs:
                if client_addr not in self.tbl:
                    self.tbl[client_addr] = deque([], self.MOV_AVG_WND)

            # update tx bytes
            for client_addr in client_addrs:
                cl_tx_bytes = self.app.getMACTxBytesStation(client_addr)
                self.tbl[client_addr].append(cl_tx_bytes * 8)

            time.sleep(self.sample_interval)

class AppMockup():

    def __init__(self):
        self.stas = ['11:11:11:11:11:11', '22:22:22:22:22:22']
        self.lastMACTxBytesStation = {}
        self.hostname = 'jayto'

    def getTxBitrateStation(self, client_addr):
        if client_addr == self.stas[0]:
            return 54
        if client_addr == self.stas[1]:
            return 18

    def getMacAddrAssociatedClients(self):
        return self.stas

    def getMACTxBytesStation(self, client_addr):
        if client_addr not in self.lastMACTxBytesStation:
            self.lastMACTxBytesStation[client_addr] = randint(1e5,1e6)
        else:
            self.lastMACTxBytesStation[client_addr] = self.lastMACTxBytesStation[client_addr] + randint(1e5,1e6)

        return self.lastMACTxBytesStation[client_addr]

if __name__ == "__main__":

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    app = AppMockup()
    rts_algo = ReadinessToServe(app)
    rts_algo.daemon = True
    rts_algo.start()

    rts_algo.infoAvBackhaulMap['foo'] = {}
    rts_algo.infoAvBackhaulMap['foo']['av_dl_backhaul'] = 12
    rts_algo.infoAvBackhaulMap['foo']['av_ul_backhaul'] = 6
    rts_algo.infoAvBackhaulMap['bar'] = {}
    rts_algo.infoAvBackhaulMap['bar']['av_dl_backhaul'] = 22
    rts_algo.infoAvBackhaulMap['bar']['av_ul_backhaul'] = 23
    time.sleep(3)
    rssi = -70
    probe_reply_tx_power = rts_algo.calculate_preply_tx_power(rssi)

    print "probe_reply_tx_power: ", str(probe_reply_tx_power)
