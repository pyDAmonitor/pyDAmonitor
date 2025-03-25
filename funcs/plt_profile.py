import matplotlib.pyplot as plt

def plt_profile(data, zticks, title, figname=None):
    plt.plot(data, zticks)
    plt.grid(linestyle = ":")
    plt.title(title)
    if figname:
        plt.savefig(figname, dpi=100, bbox_inches = 'tight')
    else:
        plt.show()
