import argparse
import json
import networkx as nx
from itertools import permutations 

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


def num_edges_in_partition(G, partition):
    edges = [e for e in G.edges(partition) if e[0] in partition and e[1] in partition]
    return len(edges)


def weighted_size(args, G, p):
    size = 0
    for n in p:
        if 'AND' in n:
            size += args.and_cost
        elif 'XOR' in n:
            size += args.xor_cost
        elif 'INV' in n:
            size += args.inv_cost

    return size


def default_size(args, G, p):
    return len(p)


def partition_cost(args, G, n_partitions, p_size, G_size, gamma=None):
    if not gamma:
        gamma = args.gamma
    alpha = nx.number_of_edges(G) * ((n_partitions**(gamma-1)) / (G_size**gamma))

    return alpha * (p_size**gamma)


def g(G, partition_list, args):
    result = 0

    partition_size = default_size
    if args.weighted_size:
        partition_size = weighted_size

    for p in partition_list:
        n_partitions = len(partition_list)
        p_view = nx.subgraph_view(G, filter_node = lambda n: n in p)
        p_view = p_view.to_undirected()

        cost = num_edges_in_partition(G, p) - \
            partition_cost(args, G, n_partitions, partition_size(args, G, p), partition_size(args, G, G))
        result += cost

    return result


def delta_g(G, vertex, partition_idx, partition_list, args):

    g_without_v = g(G, partition_list, args)
    
    partition_list[partition_idx].append(vertex)
    g_with_v = g(G, partition_list, args)
    partition_list[partition_idx].remove(vertex)

    return g_with_v - g_without_v


def vertex_assignment(G, vertex, partition_list, args):

    max_partition = 0
    max_dg = -float("inf")

    for i in range(len(partition_list)):
        dg = delta_g(G, vertex, i, partition_list, args)
        if dg > max_dg:
            max_dg = dg
            max_partition = i

    return max_partition


def fennel(G, args):

    n_partitions = args.partitions
    partitions = [[] for i in range(n_partitions)]

    for i,v in enumerate(G):
        print(i)
        if "INPUT" in v or "OUTPUT" in v:
            continue

        assignment = vertex_assignment(G, v, partitions, args)

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
parser.add_argument("--and_cost", default=8, type=int, help="AND gate cost")
parser.add_argument("--xor_cost", default=2, type=int, help="XOR gate cost")
parser.add_argument("--inv_cost", default=1, type=int, help="INV gate cost")
parser.add_argument("--partitions", default=3, type=int, help="number of graph partitions")
parser.add_argument("--weighted_size", action="store_true")
parser.add_argument("--output_influence", action="store_true")

args = parser.parse_args()

with open(args.in_json_file, 'r') as f:
    graph = json.load(f)

G = to_networkx(graph)

# Do the algorithm
G_cut, partitions = fennel(G, args)

output_graph = from_networkx(G_cut, partitions)

with open(args.out_json_file, 'w') as f:
    json.dump(output_graph, f)

