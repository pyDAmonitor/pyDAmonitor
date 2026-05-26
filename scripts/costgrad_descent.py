#!/usr/bin/env python
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
matplotlib.use('AGG')


def main():

    mfile = './minimization.txt'

    print('read minimization file=', mfile)

    blank_line_numbers = []
    with open(mfile, 'r') as f:
        for i, line in enumerate(f):
            if not line.strip():  # checks if the line is empty or just whitespace
                blank_line_numbers.append(i)

    print('first blank line found:', blank_line_numbers[0])

    half_rows = blank_line_numbers[0] - 2

    print(half_rows)
    data1 = pd.read_csv(mfile, header=1, skipinitialspace=True, nrows=half_rows, sep=' ')

    y = data1['resNorm']
    x = data1['i']
#    print(y)
    imfile = './resnorm1'
    plt.plot(x, y, '-o', c='black', linewidth=2.0, marker="", label='resNorm')
    plt.xlabel('Number of iterations', fontsize=20)
    plt.ylabel('resNorm', fontsize=20)
    plt.title('resNorm', fontsize=20)
    plt.savefig(imfile)
    plt.close()

    imfile = './cost1'
    y = data1['J']
    plt.plot(x, y, '-o', c='red', linewidth=2.0, marker="", label='J')
    y = data1['Jb']
    plt.plot(x, y, '-o', c='green', linewidth=2.0, marker="", label='Jb')
    y = data1['JoJc']
    plt.plot(x, y, '-o', c='blue', linewidth=2.0, marker="", label='JoJc')
    plt.xlabel('Number of iterations', fontsize=20)
    plt.ylabel('Cost function', fontsize=20)
    plt.title('Cost Function', fontsize=20)
    plt.legend(loc="upper right", fontsize=10)
    plt.savefig(imfile)


if __name__ == '__main__':
    main()
