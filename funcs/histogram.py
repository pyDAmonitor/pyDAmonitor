import os
import pandas as pd
import matplotlib.pyplot as plt

def histogram(group, bin_size, xlabel, title, fig_name=None):
    bins = range( int(group.min()), int(group.max())+bin_size, bin_size)
    plt.figure()
    plt.hist(group, bins=bin_size, edgecolor='black')
    plt.xlabel(xlabel)
    plt.ylabel('Frequency')
    plt.title(title)
    plt.xticks(bins)
    print(bins)
    if fig_name:                                                                                                                                                       
        plt.savefig(fig_name, dpi=250, bbox_inches='tight')
    else:
        plt.show()
