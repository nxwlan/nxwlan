
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

if __name__ == "__main__":

    """
    (0) Constants
    """
    # mac mac layer rate we can get
    max_tx_power_dbm = 24 # dBm
    default_tx_power_dbm = max_tx_power_dbm # dBm
    low_p_rx_dbm = -90 #dBm
    high_p_rx_dbm = -50 #dBm

    delta_p_rx_dbm = high_p_rx_dbm - low_p_rx_dbm

    p_ctrl = ProbeReplyTxPowerCtrl(max_tx_power_dbm, default_tx_power_dbm, low_p_rx_dbm, high_p_rx_dbm)

    hap_p_rx_dbm = -55 # dBm
    vap_p_rx_dbm = -70 # dBm

    prio = (1, 0.2)

    hap_tx_power_dbm_adapted = p_ctrl.calc_tx_power(hap_p_rx_dbm, prio[0])
    vap_tx_power_dbm_adapted = p_ctrl.calc_tx_power(vap_p_rx_dbm, prio[1])

    print "*** hap_tx_power_dbm_adapted", hap_tx_power_dbm_adapted
    print "*** vap_tx_power_dbm_adapted", vap_tx_power_dbm_adapted

    #if prio[0] <= prio[1]:
    #    assert(hap_p_rx_dbm_after <= vap_p_rx_dbm_after)