#!/usr/bin/env python
# flake8: noqa
from netCDF4 import Dataset
import matplotlib.axes as maxes
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
import os
import sys
import pandas as pd
import cartopy.crs as ccrs
from cartopy.mpl.ticker import (LongitudeFormatter, LatitudeFormatter,
                                LatitudeLocator, LongitudeLocator)
from collections.abc import Iterable
import numpy as np
import matplotlib
matplotlib.use('AGG')

def main():

    mfile = './minimization.txt'

    i = []
    resNorm = []
    J = []
    Jb = []
    JoJc = []

    print('read minimization file=', mfile)

    total_rows = sum(1 for line in open(mfile))
    half_rows = total_rows // 2 - 3
    print(half_rows)
    data1 = pd.read_csv(mfile,header=1,skipinitialspace=True,nrows=half_rows,sep=' ')

    y=data1['resNorm']
    x=data1['i']
#    print(y)
    imfile='./resnorm1'
    plt.plot(x,y,'-o',c='black',linewidth=2.0,marker="",label='resNorm')
    plt.xlabel('Number of iterations',fontsize=20)
    plt.ylabel('resNorm',fontsize=20)
    plt.title('resNorm',fontsize=20)
    plt.savefig(imfile)
    plt.close()

    imfile='./cost1'
    y=data1['J']
    plt.plot(x,y,'-o',c='red',linewidth=2.0,marker="",label='J')
    y=data1['Jb']
    plt.plot(x,y,'-o',c='green',linewidth=2.0,marker="",label='Jb')
    y=data1['JoJc']
    plt.plot(x,y,'-o',c='blue',linewidth=2.0,marker="",label='JoJc')
    plt.xlabel('Number of iterations',fontsize=20)
    plt.ylabel('Cost function',fontsize=20)
    plt.title('Cost Function',fontsize=20)
    plt.legend(loc="upper left",fontsize=10)
    plt.savefig(imfile)

if __name__ == '__main__':
    main()
