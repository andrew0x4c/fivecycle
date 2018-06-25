# Copyright (c) Andrew Li 2018. This file is licensed under the GPLv3.
# See https://github.com/andrew0x4c/fivecycle for more information,
# including the full LICENSE file.

from matplotlib import pyplot as plt
import fivecycle as fc

# visualizes a list of instructions

palette = [
    "red", "green", "blue", "orange",
    "purple", "yellow", "cyan", "magenta",
]

def plot(insts, colors=palette, default="brown"):
    plt.clf()
    for i, inst in enumerate(insts):
        if inst.cond is not None and inst.cond < len(colors):
            color = colors[inst.cond]
        else:
            color = default
        for x in range(5):
            plt.plot([i, i+1], [x+1, inst.if1(x)+1], color, linewidth=2)
        for x in range(5):
            plt.plot([i, i+1], [x+1, inst.if0(x)+1], "black", linewidth=2)
        plt.text(i+0.5, 0.5, str(inst.cond), fontsize=12,
            horizontalalignment='center', verticalalignment='center')
    plt.axis([-1, len(insts)+1, 0, 6])
