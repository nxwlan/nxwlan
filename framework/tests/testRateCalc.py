import logging

def rel_airtime(R, k):

    Rtmp = [1.0 / r for r in R]

    gamma = (1.0/R[k]) / sum(Rtmp)

    return gamma

def eff_data_rate(gamma_k, R_k):

    eff_rate_k = gamma_k * R_k

    return eff_rate_k


class WifiCapacityEstimator():
    def __init__(self, max_mac_rate):
        self.max_mac_rate = max_mac_rate

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
            print("R:PHY; {}".format(str(r_phy)))
            #mac_rate = 54.0
            mac_rate = mac_rate + (1.0 / r_phy)

        nac_rate = 1.0 / mac_rate
        print("MAC Rate (Wifi Only): {}".format(str(nac_rate)))

        # take minimum of available capacity of wireless and backhaul
        nac_rate = min(nac_rate, av_backhaul/1e6)
        print("MAC Rate (WiFi + Backhaul):{} ".format(str(nac_rate)))
        return nac_rate

    def get_normalized(self, per_client_phy_rate, av_backhaul):
        return min(1.0, self.calc(per_client_phy_rate, av_backhaul) / float(self.max_mac_rate))



if __name__ == "__main__":

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    #R = (11,11,450,450)
    R = (6,12)

    for ii in range(len(R)):
        gamma_k = rel_airtime(R, ii)
        print "gamma_%d: %s" % (ii, str(gamma_k))
        eff_rate_k = eff_data_rate(gamma_k, R[ii])
        print "eff_rate_%d: %s" % (ii, str(eff_rate_k))


    ce = WifiCapacityEstimator(36.0)

    old = ce.calc(R, 1e10)

    print "old: %s" % str(old)