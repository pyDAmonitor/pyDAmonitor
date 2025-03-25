from jdiag import get_valid_data
from plt_profile import plt_profile
import numpy as np


def fit_rate(data, dz):
    oman = get_valid_data(data, "oman")
    ombg = get_valid_data(data, "ombg")
    height = get_valid_data(data, "height")
    print("bias: oma=", np.mean(oman), "omb=", np.mean(ombg))

    rms_a = np.sqrt(np.mean(oman**2))
    rms_b = np.sqrt(np.mean(ombg**2))
    print("rms : oma=", rms_a, "omb=", rms_b)
    print("fit rate = ", (rms_b - rms_a) / rms_b)

    max_hgt = max(height)
    max_ztick = ((max_hgt // dz) + 1) * dz
    min_ztick = 0
    zticks = range(min_ztick, max_ztick, dz)
    print(zticks)

    ratio = np.empty(len(zticks))
    for i, hgt in enumerate(zticks):
        h1 = hgt
        h2 = h1 + dz
        tmp_a = oman[(height[:] >= h1) & (height[:] < h2)]
        tmp_b = ombg[(height[:] >= h1) & (height[:] < h2)]
        bias_a = np.mean(tmp_a)
        bias_b = np.mean(tmp_b)
        rms_a = np.sqrt(np.mean(tmp_a**2))
        rms_b = np.sqrt(np.mean(tmp_b**2))
        ratio[i] = (rms_b - rms_a) / rms_b
        print(i, rms_a, rms_b, ratio[i])

    plt_profile(ratio, zticks, "fit rate")
