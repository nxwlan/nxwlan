"""
Using table:
11-03-0845-01-000n-11-03-0845-00-000n-receiver-sensitivity-tables-mimo-ofdm.ppt
slide 10
"""

class PhyDataRateCalculator():
    def __init__(self):
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

if __name__ == "__main__":

    pc = PhyDataRateCalculator()
    rate = pc.get_phy_bitrate(-72)
    print "rate:", rate