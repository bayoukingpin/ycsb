#!/usr/bin/python
import csv

import sys

# import pkg_resources
# pkg_resources.require("matplotlib==1.3.x")
from matplotlib.offsetbox import TextArea, Bbox

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


def load_series(fin):

    # all series is sorted, there is no need to use dictionaries
    draw_name = ""
    draw_rd_lat = [[],[]] # x and y for read latency
    draw_up_lat = [[],[]] # x and y for update latency
    draw_th_put = [[],[]] # x and y for throughput
    # the block number, 0 - read, 1 - update, 2 - throughput
    # see /timeseries_merge.py:70
    block = 0
    reader = csv.reader(fin, dialect='excel-tab')
    for items in reader:
        if len(items) == 0:
            block += 1
        else:
            if block == 0:
                draw_name = items[0]
            elif block == 1:
                draw_rd_lat[0].append(int(items[0]))
                draw_rd_lat[1].append(float(items[1]))
            elif block == 2:
                draw_up_lat[0].append(int(items[0]))
                draw_up_lat[1].append(float(items[1]))
            else:
                draw_th_put[0].append(int(items[0]))
                draw_th_put[1].append(float(items[1]))
    # dead birds falling from the sky...
    # maybe use dict?
    return (draw_name, draw_rd_lat, draw_up_lat, draw_th_put)


def draw():
    if len(sys.argv) > 1:
        # filename passed
        with open(sys.argv[1]) as fin:
            (name, drlt, dult, dthr) = load_series(fin)
    else:
        # from stdin
        (name, drlt, dult, dthr) = load_series(sys.stdin)
    min_x = min(min(drlt[0]), min(dult[0]), min(dthr[0]))
    max_x = max(max(drlt[0]), max(dult[0]), max(dthr[0]))
    xndown = 600000 # the time for node down
    xnup = 1200000   # the time for node up
    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    plt.grid(True)
    plt.plot(dthr[0], dthr[1], 'r')
    plt.xlim([min_x, max_x])
    plt.xlabel('Execution time (ms)')
    plt.ylabel('Throughput (ops/sec)')
    (ymin, ymax) = plt.ylim()
    ax1.axvline(x=xndown, ymin=ymin, ymax=ymax, linestyle='--')
    ax1.axvline(x=xnup, ymin=ymin, ymax=ymax, linestyle='--')
    ax1.annotate('node down', xy=(xndown, ymax), xytext=(xndown - 300000, ymax * 1.03333),
                 ha='center', va='bottom',
                 bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3),
                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=-0.5',
                                 color='red'))
    ax1.annotate('node up', xy=(xnup, ymax), xytext=(xnup + 300000, ymax * 1.03333),
                 ha='center', va='bottom',
                 bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3),
                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.5',
                                 color='red'))
    # ax1.text(600000, ymax, 'node down')
    # ax1.text(650000, ymax, 'node up')
    ax2 = fig.add_subplot(212)
    plt.grid(True)
    plt.plot(drlt[0], drlt[1], 'b', label='Read latency')
    plt.plot(dult[0], dult[1], 'g', label='Update latency')
    plt.xlim([min_x, max_x])
    plt.ylim([0, 15])
    plt.xlabel('Execution time (ms)')
    plt.ylabel('Latency (ms)')
    fontP = FontProperties()
    fontP.set_size('small')
    ax2.legend(prop=fontP)
    # fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    # name = "/home/nick/buffer/Aerospike/XGraphs/%s.png" % name
    name = "%s.png" % name
    fig.savefig(name, dpi=80)

    # plt.show()

if __name__ == "__main__":
    draw()
