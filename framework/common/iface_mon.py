import time
import logging
import threading
import psutil #network interface monitoring
from common.speedtest import speedtest

class InterfaceMonitor(threading.Thread):
    def __init__(self, group=None, target=None, name=None, verbose=None, iface='eth0', interval=1, window=10):
        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        self.log = logging.getLogger("{module}.{name}".format(
            module=self.__class__.__module__, name=self.__class__.__name__))

        self.connectionMeasured = False

        #parameters
        self.iface = iface
        self.interval = interval
        self.window = window

        #capacity
        self.ping = None
        self.max_dl = None
        self.max_ul = None

        #current
        self.lastStats = None
        self.dl_samples = []
        self.ul_samples = []
        self.cur_ul = None
        self.cur_dl = None

        #available bw
        self.available_dl = None
        self.available_ul = None

    def run(self):
        # Measure maximal Backbone capacity
        self.measure_max_bn_capacity()

        # Measure network interface tx/rx 
        while True:
            self.monitor_iface_speed()
            time.sleep(self.interval)
        return

    def get_current_dl(self):
        return self.cur_dl

    def get_current_ul(self):
        return self.cur_ul

    def get_avaiable_dl(self):
        return self.available_dl

    def get_avaiable_ul(self):
        return self.available_ul

    """
    Measure maximal Backbone capacity
    """
    def measure_max_bn_capacity(self):
        self.log.info('Measure max DL and UL bandwidth....')

        [self.ping, self.max_dl, self.max_ul] = speedtest()
        #self.max_dl = 100000000
        #self.max_ul = 100000000
        self.log.info('iface: {} - MAX - DL: {} bps, UL: {} bps'.format(self.iface, self.max_dl, self.max_ul))
        self.connectionMeasured = True

    """
    Measure network interface tx/rx 
    """
    def monitor_iface_speed(self):
        stats = psutil.net_io_counters(pernic=True)
        stats = stats[self.iface]

        if not self.lastStats:
            self.lastStats = stats
            return

        #add new sample
        self.dl_samples.append((stats.bytes_recv - self.lastStats.bytes_recv) * 8)
        self.ul_samples.append((stats.bytes_sent - self.lastStats.bytes_sent) * 8)
        self.lastStats = stats

        # move window
        if len(self.dl_samples) > self.window:
            del self.dl_samples[0]
            del self.ul_samples[0]
        
        #calculate
        self.cur_dl = sum(self.dl_samples) / len(self.dl_samples)
        self.cur_ul = sum(self.ul_samples) / len(self.ul_samples)
            
        self.available_dl = self.max_dl - self.cur_dl
        self.available_ul = self.max_ul - self.cur_ul

        #print
        self.log.debug('iface: {} - current   - DL: {} bps, UL: {} bps'.format(self.iface, self.cur_dl, self.cur_ul))
        self.log.debug('iface: {} - available - DL: {} bps, UL: {} bps'.format(self.iface, self.available_dl, self.available_ul))