#!/usr/bin/python

from __future__ import print_function
import os
import re

import sys

# import pkg_resources
# print(pkg_resources.get_distribution("matplotlib").version)

def avg(seq):
    return sum(seq) / float(len(seq))

def same(x): return x

def scale1k(x) : return x / 1000.0




def merge():
    """grab all *.out, extract statistics from there and merge into TSV file """
    throughput = {}
    update_latency = {}
    read_latency = {}
    items = filter(lambda x: str(x).endswith('.out'), os.listdir('.'))
    # common_name is the name of items without '-ci' part, e.g.
    # 2013-02-07_21-40_couchbase_workloada_31250
    # then we try to cut off some parts
    common_name = os.path.commonprefix(items)[:-2]
    db_name = "unknown"
    # remove date-time and database name, since it is already there
    m = re.search(r'\d{4}-\d{2}-\d{2}_\d+-\d+_([^_]+)_(.+)', common_name)
    if m is not None:
        common_name = m.group(2)
        db_name = m.group(1)
    the_plist = split_path(os.getcwd())
    the_plist.reverse()
    the_plist = map(lambda s: s.lower(), the_plist)
    repl_type = find_set(["sync", "async"], the_plist, 4, "async")
    # find in the_plist first element that contains "failover" word,
    # usually it is "failover_ram" or "failover_ssd"
    def contains_failover(s):
        return 'failover' in s
    ram_or_ssd = next((x for x in the_plist if contains_failover(x)), "failover")
    # now combine the name of the graph
    # graph_name ~ 'aerospike-async-failover_ram-workloada_25000'
    graph_name = '-'.join([db_name, repl_type, ram_or_ssd, common_name, the_plist[0]])
    # gather stats from all files=items
    for item in items:
        with open(item) as f:
            for line in f:
                if line.startswith('[UPDATE]') or line.startswith('[READ]'):
                    items = line.split(',')
                    if len(items) == 4:
                        (op, timestamp, lat, thr) = items
                        timestamp = int(timestamp)
                        #if timestamp == 0:
                        #   print items
                        lat = float(lat) / 1000.0
                        thr = thr.strip().split(' ', 1)[0]
                        try:
                            thr = float(thr)
                        except ValueError:
                            #For "[UPDATE], 1575400, 16432.262857142858, 5250.0Reconnecting to the DB..." line
                            thr = float(re.search('\d+\.\d+', thr).group(0))
                        thr_stats = throughput.get(timestamp, 0)
                        thr_stats += thr
                        throughput[timestamp] = thr_stats
                        # default latensy 0 will not work properly
                        # hence this statement is totally wrong:
                        if (op == '[READ]'):
                            stats1 = read_latency.get(timestamp, [])
                            stats1.append(lat)
                            read_latency[timestamp] = stats1
                        elif (op == '[UPDATE]'):
                            stats2 = update_latency.get(timestamp, [])
                            stats2.append(lat)
                            update_latency[timestamp] = stats2
    #for (timestamp, thr) in OrderedDict(sorted(throughput.items(), key=lambda t: t[0])).items():
    if len(sys.argv) > 1:
        # filename passed, to filename
        with open(sys.argv[1], 'w') as f:
            flush_series(f, graph_name, read_latency, update_latency, throughput)
    else:
        # to stdout
        flush_series(sys.stdout, graph_name, read_latency, update_latency, throughput)

def split_path(path, maxdepth=20):
    ( head, tail ) = os.path.split(path)
    return split_path(head, maxdepth - 1) + [ tail ] \
        if maxdepth and head and head != path \
        else [ head or tail ]

def find_set(words, the_list, max_depth, default = ""):
    words_set = set(words)
    local_list = the_list[0:max_depth]
    for word in local_list:
        if word in words_set:
            return word
    return default

def avg_convert(the_dict):
    # post-processing for latencies goes here
    list1 = the_dict.items()
    list2 = [(x, avg(y)) for (x, y) in list1 if len(y) > 0]
    # remove empty elements
    list2.sort(key=lambda (x, y): x)
    # convert each (sub)list to average
    return list2


def flush_series(f, graph_name, read_latency, update_latency, throughput):
    # write graph name as a first piece of data
    print(graph_name, file=f)
    print('', file=f)
    # block with read latency
    for t in avg_convert(read_latency):
        print(tab_str(t), file=f)
        # skip line to mark the end of the block
    print('', file=f)
    # block with update latency
    for t in avg_convert(update_latency):
        print(tab_str(t), file=f)
        # skip line to mark the end of the block
    print('', file=f)
    # sort for timeseries.draw
    thr_list = throughput.items()
    thr_list.sort(key=lambda (x, y): x)
    for t in thr_list:
        print(tab_str(t), file=f)

def tab_str(seq):
    return '\t'.join(map(str, seq))

if __name__=='__main__':
    merge()
