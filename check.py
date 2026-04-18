import numpy as np
timestamps = [0, 0.5, 1.0]
bin_centers = np.arange(0.25, 10.0, 0.5)
for ts in timestamps:
    idx = np.searchsorted(bin_centers, ts) - 1
    print(ts, idx)