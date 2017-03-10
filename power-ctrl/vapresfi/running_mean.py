import numpy as np

class RunningMeanCalculator():
    def __init__(self):
        pass

    def running_mean(self, x, N):
        cumsum = np.cumsum(np.insert(x, 0, 0))
        return (cumsum[N:] - cumsum[:-N]) / N


if __name__ == "__main__":

    rm = RunningMeanCalculator()

    x = [3e6, 3.4e6, 2.5e6, 2.9e6, 4e6, 4.5e6]
    #x = [1e6, 1e6, 1e6, 1e6, 1e6]
    N = 3

    val = rm.running_mean(x, N)

    print "val: ", val[-1] / 1e6