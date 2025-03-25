import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker


def histogram(data, bin_size, n_xticks, xlabel, title, fig_name=None):
    bins = np.arange(int(data.min()), int(data.max()) + bin_size, bin_size)
    plt.figure()
    plt.hist(data, bins=bins, edgecolor="black")
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")
    plt.title(title)
    # Set x-axis locator to limit number of ticks
    plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=n_xticks))  # Adjust number of labels dynamically
    # plt.xticks(bins)
    plt.xticks(rotation=45)
    if fig_name:
        plt.savefig(fig_name, dpi=250, bbox_inches="tight")
    else:
        plt.show()
