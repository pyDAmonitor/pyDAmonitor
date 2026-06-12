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
    plt.ylabel('Residual norm', fontsize=20)
    plt.title('Residual Norm, Loop 1', fontsize=20)
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
    plt.title('Cost Function, Loop 1', fontsize=20)
    plt.legend(loc="upper right", fontsize=10)
    plt.savefig(imfile)
    plt.close()

    first_row = blank_line_numbers[0] + 2
    skip_rows = blank_line_numbers[0] + 3

    print('beginning of second loop:', first_row)

    half_rows2 = blank_line_numbers[1] - skip_rows

    print(half_rows2)

    data2 = pd.read_csv(mfile, header=first_row, skip_blank_lines=False, skipinitialspace=True, nrows=half_rows2, sep=' ')

    y = data2['resNorm']
    x = data2['i']
    imfile = './resnorm2'
    plt.plot(x, y, '-o', c='black', linewidth=2.0, marker="", label='resNorm')
    plt.xlabel('Number of iterations', fontsize=20)
    plt.ylabel('Residual norm', fontsize=20)
    plt.title('Residual Norm, Loop 2', fontsize=20)
    plt.savefig(imfile)
    plt.close()

    imfile = './cost2'
    y = data2['J']
    plt.plot(x, y, '-o', c='red', linewidth=2.0, marker="", label='J')
    y = data2['Jb']
    plt.plot(x, y, '-o', c='green', linewidth=2.0, marker="", label='Jb')
    y = data2['JoJc']
    plt.plot(x, y, '-o', c='blue', linewidth=2.0, marker="", label='JoJc')
    plt.xlabel('Number of iterations', fontsize=20)
    plt.ylabel('Cost function', fontsize=20)
    plt.title('Cost Function, Loop 2', fontsize=20)
    plt.legend(loc="upper right", fontsize=10)
    plt.savefig(imfile)


if __name__ == '__main__':
    main()
