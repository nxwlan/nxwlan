from capacity import CapacityEstimator
from power_ctrl import ProbeReplyTxPowerCtrl
from rate_calc import PhyDataRateCalculator
from running_mean import RunningMeanCalculator

"""
    TODO: to be replaced by real call!!!!
"""
def perform_mockup_station_dump():
    file = open('station_dump_example.txt', 'r')
    return file.read()

"""
    ResFi API call:
    Information about associated STAs. The return value has the following structure:
    mac_addr -> stat_key -> list of (value, unit)
"""
def getInfoOfAssociatedSTAs():
    try:
        #command = 'iw dev ' + config.WIRELESS_INTERFACE + ' station dump'
        #sout = self.run_command(command)
        sout = perform_mockup_station_dump()

        # mac_addr -> stat_key -> list of (value, unit)
        res = {}
        sout_arr = sout.split("\n")

        for line in sout_arr:
            s = line.strip()
            if s == '':
                continue
            if "Station" in s:
                arr = s.split()
                mac_addr = arr[1].strip()
                res[mac_addr] = {}
            else:
                arr = s.split(":")
                key = arr[0].strip()
                val = arr[1].strip()
                arr2 = val.split()
                val2 = arr2[0].strip()
                if len(arr2) > 1:
                    unit = arr2[1].strip()
                else:
                    unit = None
                res[mac_addr][key] = (val2, unit)
        return res
    except Exception as e:
        raise Exception("An error occurred: %s" % e)


def get_tx_bitrate_station(mac_addr):

    tmp = getInfoOfAssociatedSTAs()

    return float(tmp[mac_addr]['tx bitrate'][0])

if __name__ == "__main__":

    """
    (0) Constants
    """
    # mac mac layer rate we can get
    max_mac_rate = 54
    max_tx_power_dbm = 24 # dBm
    default_tx_power_dbm = max_tx_power_dbm # dBm
    low_p_rx_dbm = -90 #dBm
    high_p_rx_dbm = -50 #dBm
    min_client_avg_tx_rate_mbps = 1 # clients mit tx bitrate of min 1 Mbps are treated as fat clients -> we will compete with them for medium

    """
    (1) Identify the phy rate of each client having long-lived flows
    """

    """
    time sampled (1 Hz) tx bytes from station dump
    TODO: replace by periodic calls to station dump
    """
    # time samples tx bytes for each already served client
    hap_client_a_tx_bits = [3e6, 3.4e6, 2.5e6, 2.9e6, 4e6, 4.5e6] * 8
    vap_client_a_tx_bits = [4e6, 3.4e6, 2.9e6, 2.3e6, 3.3e6, 4.2e6] * 8
    # moving average window
    N = 3

    rm = RunningMeanCalculator()
    hap_client_a_mac_addr = 'b8:a3:86:96:96:8a'
    hap_client_a_avg_tx_rate_mbps = rm.running_mean(hap_client_a_tx_bits, N)[-1] / 1e6
    vap_client_a_mac_addr = 'aa:bb:86:96:96:cc'
    vap_client_a_avg_tx_rate_mbps = rm.running_mean(vap_client_a_tx_bits, N)[-1] / 1e6

    print "hap_client_a_avg_tx_rate_mbps: ", hap_client_a_avg_tx_rate_mbps
    print "hap_client_b_avg_tx_rate_mbps: ", vap_client_a_avg_tx_rate_mbps

    hap_client_phy_rates = []
    if hap_client_a_avg_tx_rate_mbps >= min_client_avg_tx_rate_mbps:
        # get tx bitrate from station dump
        hap_client_a_tx_bitrate = get_tx_bitrate_station(hap_client_a_mac_addr)
        hap_client_phy_rates.append(hap_client_a_tx_bitrate)

    vap_client_phy_rates = []
    if vap_client_a_avg_tx_rate_mbps >= min_client_avg_tx_rate_mbps:
        # get tx bitrate from station dump
        vap_client_a_tx_bitrate = get_tx_bitrate_station(vap_client_a_mac_addr)
        vap_client_phy_rates.append(vap_client_a_tx_bitrate)


    """
    (2) Measured rx power from probe requests
    """
    hap_p_rx_dbm = -55 # dBm
    vap_p_rx_dbm = -70 # dBm

    """
    (3) Calc expected phy rate of new client towards HAP and VAP
    """
    pc = PhyDataRateCalculator()
    client_hap_phy_rate = pc.get_phy_bitrate(hap_p_rx_dbm)
    print "client_hap_phy_rate:", client_hap_phy_rate
    client_vap_phy_rate = pc.get_phy_bitrate(vap_p_rx_dbm)
    print "client_vap_phy_rate:", client_vap_phy_rate

    c = CapacityEstimator(max_mac_rate)

    """
    (3) Get priority
    """
    hap_client_phy_rates.append(client_hap_phy_rate)
    mac_rate_hap_norm = c.get_normalized(hap_client_phy_rates)
    vap_client_phy_rates.append(client_vap_phy_rate)
    mac_rate_vap_norm = c.get_normalized(vap_client_phy_rates)

    print "mac_rate_hap_norm: ", mac_rate_hap_norm
    print "mac_rate_vap_norm: ", mac_rate_vap_norm

    p_ctrl = ProbeReplyTxPowerCtrl(max_tx_power_dbm, default_tx_power_dbm, low_p_rx_dbm, high_p_rx_dbm)

    hap_tx_power_dbm_adapted = p_ctrl.calc_tx_power(hap_p_rx_dbm, mac_rate_hap_norm)
    vap_tx_power_dbm_adapted = p_ctrl.calc_tx_power(vap_p_rx_dbm, mac_rate_vap_norm)

    print "*** hap_tx_power_dbm_adapted", hap_tx_power_dbm_adapted
    print "*** vap_tx_power_dbm_adapted", vap_tx_power_dbm_adapted
