

class CapacityEstimator():
    def __init__(self, max_mac_rate):
        self.max_mac_rate = max_mac_rate

    def calc(self, per_client_phy_rate):
        """
        The slowest clients data rate represents an upper boundary of every clients long term throughput.
        """

        mac_rate = 0.0
        for r_phy in per_client_phy_rate:
            mac_rate = mac_rate + (1.0 / r_phy)

        nac_rate = 1.0 / mac_rate

        return nac_rate

    def get_normalized(self, per_client_phy_rate):
        return min(1.0, self.calc(per_client_phy_rate) / self.max_mac_rate)

if __name__ == "__main__":

    """
    (0) Constants
    """
    # mac mac layer rate we can get
    max_mac_rate = 54

    """
    (1) Identify the phy rate of each client having long-lived flows
    """
    hap_client_phy_rates = (36)
    vap_client_phy_rates = (24)

    """
    (2) Phy rate of new client towards HAP and VAP
    """
    client_hap_phy_rate = 6
    client_vap_phy_rate = 24

    c = CapacityEstimator(max_mac_rate)

    mac_rate_hap = c.calc([hap_client_phy_rates, client_hap_phy_rate])
    mac_rate_vap = c.calc([vap_client_phy_rates, client_vap_phy_rate])

    print "mac_rate_hap: ", mac_rate_hap
    print "mac_rate_vap: ", mac_rate_vap

    """
    (3) Normalize
    """
    mac_rate_hap_norm = c.get_normalized([hap_client_phy_rates, client_hap_phy_rate])
    mac_rate_vap_norm = c.get_normalized([vap_client_phy_rates, client_vap_phy_rate])

    print "mac_rate_hap_norm: ", mac_rate_hap_norm
    print "mac_rate_vap_norm: ", mac_rate_vap_norm
