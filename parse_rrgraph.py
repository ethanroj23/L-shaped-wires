from lzma import CHECK_ID_MAX
from os import R_OK
import sys
import re

import matplotlib.pyplot as plt
import numpy as np


XLOW = 0
YLOW = 1
XHIGH = 2
YHIGH = 3
R_IDX = 4
C_IDX = 5



plt.show()

if __name__ == '__main__':
    # fig = plt.figure()
    # ax = fig.add_subplot(1, 1, 1)
    # ax.set_ylabel('volts')
    # ax.set_title('a sine wave')
    # ax.set_xlabel('time (s)')
    # ax.bar([0, 1],[10, 20])
    
    # plt.savefig('test_plot.png')
    if len(sys.argv) > 1:
        part_num = sys.argv[1]
    else:
        print("Please include the part number: 50, 100 or 200")
        exit()
        
    filename = f'/home/ethan/workspaces/ethanroj23/rr_graph_folding/flat_graphs/xc7a{part_num}t_test.xml'
    count = 0
    print(f"Working on {part_num}t")

# <node capacity="1" direction="DEC_DIR" id="10981" type="CHANX"><loc ptc="17" xhigh="6" xlow="3" yhigh="6" ylow="6"/>
# <switch id="5" name="short" type="short"><timing/>
    def get_part_info(f):
        node_shorted_to = {}
        nodes = {}
        total_edges = 0
        total_non_shorted_edges = 0
        node_to_line = {}
        s = ''
        short_id = -1
        node_type_count = {}
        node_count = 0
        chanz_count = 0
        for line in f:
            if '<switch id' in line:
                if '"short"' in line:
                    short_id = re.findall('switch id="([0-9]+)"', line)[0]
                    print("Short switch id is", short_id)
            if '<node' in line:
                node_type = re.findall('type="([A-Z]+)"', line)[0]
                node_id = re.findall('id="([0-9]+)"', line)[0]
                xlow = int(re.findall('xlow="([0-9]+)"', line)[0])
                xhigh = int(re.findall('xhigh="([0-9]+)"', line)[0])
                ylow = int(re.findall('ylow="([0-9]+)"', line)[0])
                yhigh = int(re.findall('yhigh="([0-9]+)"', line)[0])
                if node_type not in node_type_count:
                    node_type_count[node_type] = 0
                node_type_count[node_type] += 1
                node_count += 1 
                nodes[node_id] = [xlow, ylow, xhigh, yhigh]
                node_to_line[node_id] = line
            if '<timing C=' in line:
                R = re.findall('R="(.+?)"', line)[0]
                C = re.findall('C="(.+?)"', line)[0]
                nodes[node_id].append(R)
                nodes[node_id].append(C)



            if '<edge' in line:
                total_edges += 1
                if f'switch_id="{short_id}"' in line:
                    source = re.findall('src_node="([0-9]+)"', line)[0]
                    sink = re.findall('sink_node="([0-9]+)"', line)[0]
                    if source not in node_shorted_to:
                        node_shorted_to[source] = []
                    node_shorted_to[source].append(sink)
                    chanz_count += 1
                else:
                    total_non_shorted_edges += 1

        # Look into shorted connections

        graph_written = {}
        write_all_plots = True
        if write_all_plots:
            max_src = list(node_shorted_to.keys())[0]
            for src in node_shorted_to:
                if len(node_shorted_to[src]) in graph_written:
                    continue
                graph_written[len(node_shorted_to[src])] = True
                fig = plt.figure()
                ax = fig.add_subplot(1, 1, 1)

                for sink in node_shorted_to[src]+[src]:
                    print(sink)

                    xpoints = np.array([nodes[sink][XLOW], nodes[sink][XHIGH]])
                    ypoints = np.array([nodes[sink][YLOW], nodes[sink][YHIGH]])
                    ax.plot(xpoints, ypoints)
                plt.savefig('plots/'+ str(len(node_shorted_to[src]))+'_'+str(src)+'.png')
                plt.close(fig)

                if len(node_shorted_to[src]) > len(node_shorted_to[max_src]):
                    max_src = src
        
        shorts_count = {}
        for src in node_shorted_to:
            count = len(node_shorted_to[src])
            if count not in shorts_count:
                shorts_count[count] = 0
            shorts_count[count] += 1
        
        
        num_shorts = []
        num_num_shorts = []
        for k, v in shorts_count.items(): 
            print(k, v)
            num_shorts.append(k)
            num_num_shorts.append(v)


        # Bar Chart Stuff
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.bar(num_shorts,num_num_shorts)
        ax.set_xlabel('Number of Shorted Nodes Per Group')
        ax.set_title(f'Shorted Nodes for XC7A{part_num}T')
        ax.set_ylabel('Number of Groups')
        plt.savefig(f'bar_plot_{part_num}.png', bbox_inches="tight")

        # Check all the node values
        print("First node")
        rc_matches = 0
        for src in node_shorted_to:
            if len(node_shorted_to[src]) != 1:
                continue
            R = nodes[src][R_IDX]
            C = nodes[src][C_IDX]
            for node in node_shorted_to[src]:
                if C != nodes[node][C_IDX] or R != nodes[node][R_IDX]:
                    print(f'{C} doesnt match {nodes[node][C_IDX]}')
                    print(f'{R} doesnt match {nodes[node][R_IDX]}')
                else:
                    rc_matches += 1
        print(f"RC matches for {rc_matches} nodes")



        



        s = f'Found {node_count} nodes\n'
        s = f"CHAN / TOTAL [{(node_type_count['CHANX']+node_type_count['CHANY']) / node_count:.2f}] nodes\n"
        s += f'Found {chanz_count} chanz nodes [{chanz_count / count:.2f}]\n'
        s += f'Found {len(node_shorted_to)}\n'
        s += f"CHANZ out of CHANX / CHANY [{chanz_count / (node_type_count['CHANX']+node_type_count['CHANY']):.2f}]"


        s += f"RRGraph Size: {(node_count*16 + total_edges*10)/1024/1024:.2f}]"
        s += f"RRGraph Size without shorted edges: {(node_count*16 + total_non_shorted_edges*10)/1024/1024:.2f}]"
        for node_type in node_type_count:
            print(f"{node_type}: {node_type_count[node_type]}")
        return s

    with open(filename, 'r') as f:
        info = get_part_info(f)

    print(info)

    