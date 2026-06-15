import math

r0 = 6356766.0

def zeta_to_isa(zeta_file, isa_file):   
    # Read geometric altitudes
    with open(zeta_file) as f:
        z = [float(line.strip()) for line in f]
        
    nsig = len(z)

    # Compute pressure at each level using ISA
    # print(nsig)
    with open(isa_file, 'w') as f:
        for i in range(1, nsig):
            h = r0 * z[i] / (r0 + z[i]) / 1.0e3
            if 0 <= h < 11:
                t = 15.0 - 6.5 * h
                p = 101325.0 * (288.15 / (t + 273.15)) ** -5.256
            elif 11 <= h < 20:
                t = -56.5
                p = 22632.064 * math.exp(-0.1577 * (h - 11.0))
            elif 20 <= h < 32:
                t = -76.5 + h
                p = 5474.889 * (216.65 / (t + 273.15)) ** 34.163
            elif 32 <= h < 47:
                t = -134.1 + 2.8 * h
                p = 868.019 * (228.65 / (t + 273.15)) ** 12.201
            f.write(f" {(p * 0.01):.7g}\n")


if __name__ == '__main__':
    zeta_file = "../data/vert_levels/L60.txt"
    isa_file = "./mpas_pave_L60.txt"
    zeta_to_isa(zeta_file, isa_file)
