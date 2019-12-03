import argparse
import json
import networkx as nx
from itertools import permutations 

GAMMA = 4

def to_networkx(graph_json):
    G = nx.DiGraph()

    for n in graph["nodes"]:
        G.add_node(n["id"])

    for l in graph["links"]:
        G.add_edge(l["source"], l["target"], weight=l["value"])

    return G

def from_networkx(G, partitions):
    nodes = []
    for n in G:
        group = 0
        for i, p in enumerate(partitions):
            if n in p:
                group = i

        nodes.append({
            "id": n,
            "group": group
        })

    links = []
    for e in G.edges():
        links.append({
            "source": e[0],
            "target": e[1],
            "value": G[e[0]][e[1]]["weight"]
        })

    return {
        "nodes": nodes,
        "links": links
    }


def c(G, n_partitions, x):
    gamma = GAMMA
    alpha = nx.number_of_edges(G) * ((n_partitions**(gamma-1)) / (nx.number_of_nodes(G)**gamma))

    return alpha * (x**gamma)


def num_edges_in_partition(G, partition):
    edges = [e for e in G.edges(partition) if e[0] in partition and e[1] in partition]
    return len(edges)


def g(G, partition_list):
    result = 0
    for p in partition_list:
        result += (num_edges_in_partition(G, p) - c(G, len(partition_list), len(p)))

    return result


def delta_g(G, vertex, partition_idx, partition_list):

    g_without_v = g(G, partition_list)
    
    partition_list[partition_idx].append(vertex)
    g_with_v = g(G, partition_list)
    partition_list[partition_idx].remove(vertex)

    return g_with_v - g_without_v


def vertex_assignment(G, vertex, partition_list):

    max_partition = 0
    max_dg = -float("inf")

    for i in range(len(partition_list)):
        dg = delta_g(G, vertex, i, partition_list)
        if dg > max_dg:
            max_dg = dg
            max_partition = i

    return max_partition


def fennel(G, n_partitions):

    partitions = [[] for i in range(n_partitions)]

    for v in G:
        if "INPUT" in v or "OUTPUT" in v:
            continue

        assignment = vertex_assignment(G, v, partitions)

        partitions[assignment].append(v)
        for pre in G.predecessors(v):
            if "INPUT" in pre:
                partitions[assignment].append(pre)

        for post in G.successors(v):
            if "OUTPUT" in post:
                partitions[assignment].append(post)

    return G, partitions
    

parser = argparse.ArgumentParser(description="Basic Fennel graph partition algorithm")
parser.add_argument("in_json_file", help="Input file location")
parser.add_argument("out_json_file", help="Output file location")
parser.add_argument("--gamma", default=4, type=float, help="gamma for intra-cluster cost function")
parser.add_argument("--partitions", default=3, type=int, help="number of graph partitions")

args = parser.parse_args()
GAMMA = args.gamma

with open(args.in_json_file, 'r') as f:
    graph = json.load(f)

G = to_networkx(graph)

# Do the algorithm
G_cut, partitions = fennel(G, args.partitions)

output_graph = from_networkx(G_cut, partitions)

with open(args.out_json_file, 'w') as f:
    json.dump(output_graph, f)

