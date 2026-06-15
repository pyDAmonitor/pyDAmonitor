import math

r0 = 6356766.0  # the earth's radius (unit: m)


def isa(altitude_file, isa_file):
    # Read geometric altitudes (unit: m) from input file
    with open(altitude_file) as f:
        z = [float(line.strip()) for line in f]

    # Compute International Standard Atmosphere (ISA) pressure at each level
    # refer to https://en.wikipedia.org/wiki/International_Standard_Atmosphere
    nsig = len(z)  # the number of vertical levels
    # print(nsig)
    with open(isa_file, 'w') as f:
        for i in range(1, nsig):
            # calculate geopotential altitude (unit: km) from given geometric altitude (unit: m)
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
            elif 47 <= h:
                print(" there is no definition for altitude greater than 47 km yet, will add in future!")
                break
            f.write(f" {(p * 0.01):.10g}\n")


if __name__ == '__main__':
    altitude_file = "../data/vert_levels/L60.txt"
    isa_file = "./mpas_pave_L60.txt"
    isa(altitude_file, isa_file)
