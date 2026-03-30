#!/usr/bin/env python
# parse data assimilation stats from the log file
#
import sys
import re


# write a list of lines into a txt file
def write2file(fname, data):
    with open(f'{fname}.txt', 'w') as outfile:
        for line in data:
            outfile.write(f'{line}\n')
    outfile.close()

# stats for each outer loop


def loop_stats(data, fname, iOuterloop):
    iterations = []
    start = -999
    end = -999
    exit_for = False
    for i, line in enumerate(data):
        if line.startswith("DRPCGMinimizer: max iter"):
            numbers = re.findall(r'\d+\.?\d*', line)
            max_iter = int(numbers[0])        # 50
            norm_reduction_target = float(numbers[1])  # 0.001
        elif line.startswith("OOPS_STATS DRPCG start"):
            start = i
        elif 'DRPCG Starting Iteration' in line:
            end = i
        elif line.startswith("DRPCGMinimizer: reduction in residual norm"):
            end = i
            norm_reduction_final = line.split("=")[1].strip()
            exit_for = True
        # ~~~~
        # print(i, start, end, line)
        if start > 0 and end > 0:
            iterations.append([data[j] for j in range(start, end)])
            start = end
            end = -999
        if exit_for:
            break
    # ~~~~~~~~~~
    minization = []
    for i, iteration in enumerate(iterations):
        dcTmp = {}
        for line in iteration:
            if "Residual norm" in line:
                numbers = re.findall(r'\d+\.?\d*', line)
                dcTmp["resNorm"] = float(numbers[1])
            elif "Quadratic cost function: J   (" in line:
                numbers = re.findall(r'\d+\.?\d*', line)
                dcTmp["J"] = float(numbers[1])
            elif "Quadratic cost function: Jb  (" in line:
                numbers = re.findall(r'\d+\.?\d*', line)
                dcTmp["Jb"] = float(numbers[1])
            elif "Quadratic cost function: JoJc(" in line:
                numbers = re.findall(r'\d+\.?\d*', line)
                dcTmp["JoJc"] = float(numbers[1])
                break
        minization.append(dcTmp)
    # write out stats for a file
    file_mode = 'w' if iOuterloop == 1 else 'a'
    with open(fname, file_mode) as outfile:
        outfile.write(f'loop{iOuterloop}: max_iter={max_iter}, norm_reduction(target={norm_reduction_target}, final={norm_reduction_final})\n')
        outfile.write(f"{'i':>3} {'resNorm':>25} {'J':>25} {'Jb':>25} {'JoJc':>25}\n")
        for i, iteration in enumerate(minization):
            outfile.write(f"{i:3} {iteration['resNorm']:25.12f} {iteration['J']:25.12f} {iteration['Jb']:25.12f} {iteration['JoJc']:25.12f}\n")
        outfile.write('\n')


def obs_counts(fname, pre_loop, loop1, loop2, oma):
    dcKnt = {}
    # -- get the raw obs count in the ioda file
    for i, line in enumerate(pre_loop):
        if 'read database' in line:
            pos = i
            break
    # ~~~~~~~~
    while pos < len(pre_loop):
        pos = pos + 5
        line = pre_loop[pos-1]
        observer, count = line.split(':')
        numbers = re.findall(r'\d+\.?\d*', line.split(':')[1])
        dcKnt[observer] = f'{numbers[1]:>8}'
        if 'read database' not in pre_loop[pos]:
            break
    # ~~~~~~~~
    # -- get the obs count for loop0 and loop1
    pos = 0
    pos2 = 0
    pos3 = 0
    for observer in dcKnt:
        pattern = rf"\b{observer}\b.*\bnlocs\b.*\bnobs\b.*\bmin\b.*\bmax\b.*\bavg\b"
        while pos < len(loop1):
            line = loop1[pos]
            if re.search(pattern, line):
                numbers = re.findall(r'\d+\.?\d*', line.split('=', 1)[1])
                dcKnt[observer] = f'{dcKnt[observer]} {numbers[0]:>8} {numbers[1]:>8}'
                break
            else:
                pos += 1
        # ~~~~~~~~~~
        # find n_loop1
        while pos2 < len(loop1):
            line = loop1[pos2]
            if f'CostJo   : Nonlinear Jo({observer}' in line:
                numbers = re.findall(r'\d+\.?\d*', line.split('=', 1)[1])
                dcKnt[observer] = f'{dcKnt[observer]} {numbers[1]:>8}'
                break
            else:
                pos2 += 1
        # ~~~~~~~~~~
        # find n_loop1
        while pos3 < len(loop2):
            line = loop2[pos3]
            if f'CostJo   : Nonlinear Jo({observer}' in line:
                numbers = re.findall(r'\d+\.?\d*', line.split('=', 1)[1])
                dcKnt[observer] = f'{dcKnt[observer]} {numbers[1]:>8}'
                break
            else:
                pos3 += 1
    # ~~~~~~~~~~~~
    with open(fname, 'w') as outfile:
        outfile.write(f"{'observer':>19} {'n_raw':>8} {'n_locs':>8} {'n_loop0':>8} {'n_loop1':>8} {'n_loop2':>8}\n")
        for key, value in dcKnt.items():
            outfile.write(f'{key:>18}: {value}\n')


#
# ***********************************************************************
# !!  MAIN starts here !!
# ***********************************************************************
# read the log file name from the command line; if not specified, default to 'log.out'
split_files = False
logfile = 'log.out'
if len(sys.argv) > 1:
    logfile = sys.argv[1]
    if "split" in logfile:
        logfile = 'log.out'
        split_files = True
if len(sys.argv) > 2 and "split" in sys.argv[2]:
    split_files = True
#
# -----------------------------------------------------------------------
# read all lines and split into different blocks
# -----------------------------------------------------------------------
config, pre_loop, loop1, loop2, oma, last = ([] for _ in range(6))
block = config  # block is a just pointer here, no data copy
with open(logfile, 'r') as infile:
    for line in infile:
        line = line.rstrip()  # strip all trailing empty spaces
        if line.startswith('OOPS_STATS ObjectCountHelper started'):
            block = pre_loop
        elif line.startswith('IncrementalAssimilation: Configuration for outer iteration 0'):
            block = loop1
        elif line.startswith('IncrementalAssimilation: Configuration for outer iteration 1'):
            block = loop2
        elif line.startswith('Variational: incremental assimilation done'):
            block = oma
        elif line.startswith('==> destruct MPAS corelist and domain:  0'):
            block = last
        # ~~~~~~
        block.append(line)
# ~~~~~~~~~~~
# write each block into a txt file when needed
if split_files:
    write2file('config', config)
    write2file('pre_loop', pre_loop)
    write2file('loop1', loop1)
    write2file('loop2', loop2)
    write2file('oma', oma)
    write2file('last', last)
# ~~~~
# write out the minimization.txt file
loop_stats(loop1, 'minimization.txt', 1)
loop_stats(loop2, 'minimization.txt', 2)
#
# write out the obs_counts.txt files
obs_counts('obs_count.txt', pre_loop, loop1, loop2, oma)
