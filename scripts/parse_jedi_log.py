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
def minimization_stats(data, fname, iOuterloop):
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
    # -------------------------------------------------------------
    # get all observers in this JEDI run
    # ~~~~~ find the first 'read database' line
    for i, line in enumerate(pre_loop):
        if 'read database' in line:
            pos = i
            break
    # ~~~~~~~~ n_ioda, n_vars, is_BT(brightness temperature)
    while pos < len(pre_loop):
        line = pre_loop[pos+4]
        observer = line.split(':')[0]
        numbers = re.findall(r'\d+\.?\d*', line.split(':')[1])
        dcKnt[observer] = {'n_ioda': numbers[1]}
        #
        line = pre_loop[pos+2]
        numbers = re.findall(r'\d+\.?\d*', line.split(':')[1])
        dcKnt[observer]['n_vars'] = numbers[0]
        if "brightnessTemperature" in line:
            dcKnt[observer]['is_BT'] = True
        else:
            dcKnt[observer]['is_BT'] = False
        #
        pos = pos + 5
        if 'read database' not in pre_loop[pos]:
            break
    # -------------------------------------------------------------
    # -- get the obs count for loop0 and loop1
    pos, pos1, pos2, pos3, posBT1, posBT2 = 0, 0, 0, 0, 0, 0
    for observer in dcKnt:
        # ~~~~~~~~ nobs
        pattern = rf"^{observer}\b.*\bnlocs\b.*\bnobs\b"
        while pos < len(loop1):
            line = loop1[pos]
            if re.search(pattern, line):
                numbers = re.findall(r'\d+\.?\d*', line.split('=', 1)[1])
                if dcKnt[observer]['is_BT']:
                    dcKnt[observer]['nobs_singleBT'] = numbers[0]
                    dcKnt[observer]['nobs'] = str(int(numbers[0]) * int(dcKnt[observer]['n_vars']))
                else:
                    dcKnt[observer]['nobs'] = numbers[0]
                break
            else:
                pos += 1
        # ~~~~~~~~ nobs_r, right after "CostJo Observations:"
        pattern = rf"^{observer} nobs\b.*\bMin\b.*\bMax\b.*\bRMS\b"
        while pos1 < len(loop1):
            line = loop1[pos1]
            if re.search(pattern, line):
                numbers = re.findall(r'\d+\.?\d*', line.split(' ', 1)[1])
                dcKnt[observer]['nobs_r'] = numbers[0]
                if dcKnt[observer]['is_BT']:
                    dcKnt[observer]['nobs_r_singleBT'] = str(int(int(numbers[0]) / int(dcKnt[observer]['n_vars'])))
                break
            else:
                pos1 += 1
        # ~~~~~~~~~~
        # n_loop1, obserr, Jo/n_1
        while pos2 < len(loop1):
            line = loop1[pos2]
            if f'CostJo   : Nonlinear Jo({observer}' in line:
                numbers = re.findall(r'\d+\.?\d*', line.split('=', 1)[1])
                dcKnt[observer]['n_loop1'] = numbers[1]
                dcKnt[observer]['Jo/n_1'] = numbers[2]
                dcKnt[observer]['obserr'] = numbers[3]
                break
            else:
                pos2 += 1
        # ~~~~~~~~~~
        # n_loop2
        while pos3 < len(loop2):
            line = loop2[pos3]
            if f'CostJo   : Nonlinear Jo({observer}' in line:
                numbers = re.findall(r'\d+\.?\d*', line.split('=', 1)[1])
                dcKnt[observer]['n_loop2'] = numbers[1]
                dcKnt[observer]['Jo/n_2'] = numbers[2]
                break
            else:
                pos3 += 1
        # ~~~~~~~~~~
        # satellite n_loop1, nloop2 per channel
        if dcKnt[observer]['is_BT']:
            while posBT1 < len(loop1):
                line = loop1[posBT1]
                if f'Jo Obs :{observer}:brightnessTemperature' in line:
                    dcKnt[observer]['ch_loop1'] = {}
                    for i in range(int(dcKnt[observer]['n_vars'])):
                        line = loop1[posBT1 + i]
                        segments = line.split(':')
                        channel = segments[2].strip().split('_')[1].strip()
                        if 'No observations' in segments[3]:
                            dcKnt[observer]['ch_loop1'][channel] = '0'
                        else:
                            numbers = re.findall(r'\d+\.?\d*', segments[3].strip())
                            dcKnt[observer]['ch_loop1'][channel] = numbers[0]
                    posBT1 += int(dcKnt[observer]['n_vars'])
                    break
                else:
                    posBT1 += 1
            # ~~~~~~~~
            while posBT2 < len(loop2):
                line = loop2[posBT2]
                if f'Jo Obs :{observer}:brightnessTemperature' in line:
                    dcKnt[observer]['ch_loop2'] = {}
                    for i in range(int(dcKnt[observer]['n_vars'])):
                        line = loop2[posBT2 + i]
                        segments = line.split(':')
                        channel = segments[2].strip().split('_')[1].strip()
                        if 'No observations' in segments[3]:
                            dcKnt[observer]['ch_loop2'][channel] = '0'
                        else:
                            numbers = re.findall(r'\d+\.?\d*', segments[3].strip())
                            dcKnt[observer]['ch_loop2'][channel] = numbers[0]
                    posBT2 += int(dcKnt[observer]['n_vars'])
                    break
                else:
                    posBT2 += 1
    # -------------------------------------------------------------
    # write out files
    with open(fname, 'w') as outfile:
        outfile.write(f"{'observer':>16} {'n_ioda':>8} {'nobs':>8} {'nobs_r':>8} {'n_loop1':>8} {'n_loop2':>8} {'obserr':>12} {'Jo/n_1':>12} {'Jo/n_2':>12}\n")
        for key in dcKnt:
            outfile.write(f'{key:>16} {dcKnt[key]["n_ioda"]:>8} {dcKnt[key]["nobs"]:>8} {dcKnt[key]["nobs_r"]:>8} {dcKnt[key]["n_loop1"]:>8}')
            outfile.write(f' {dcKnt[key]["n_loop2"]:>8} {dcKnt[key]["obserr"]:>12} {dcKnt[key]["Jo/n_1"]:>12} {dcKnt[key]["Jo/n_2"]:>12}\n')
            if dcKnt[key]['is_BT']:  # write out obs counts per each satellite channel to a seperate fie
                with open(f'{key}.txt', 'w') as satfile:
                    satfile.write(f'{key} each channel: n_ioda={dcKnt[key]["n_ioda"]:>8} nobs={dcKnt[key]["nobs_singleBT"]:>8} nobs_r={dcKnt[key]["nobs_r_singleBT"]:>8}\n')
                    satfile.write(f"{'channel':>7} {'n_loop1':>8} {'n_loop2':>8}\n")
                    for (k1, v1), (k2, v2) in zip(dcKnt[key]['ch_loop1'].items(), dcKnt[key]['ch_loop2'].items()):
                        satfile.write(f'{k1:>7} {v1:>8} {v2:>8}\n')


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
config, pre_loop, loop1, loop2, oma, final = ([] for _ in range(6))
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
            block = final
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
    write2file('final', final)
# ~~~~
# write out the minimization.txt file
minimization_stats(loop1, 'minimization.txt', 1)
minimization_stats(loop2, 'minimization.txt', 2)
#
# write out the obs_counts.txt files
obs_counts('obs_count.txt', pre_loop, loop1, loop2, oma)
