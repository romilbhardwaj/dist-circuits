import argparse
import json
import networkx as nx
from itertools import permutations 
from collections import Counter

def to_networkx(graph_json):
    G = nx.DiGraph()

    node_group_map = {}
    for n in graph["nodes"]:
        G.add_node((n["id"], n["group"]))
        node_group_map[n["id"]] = n["group"]

    for l in graph["links"]:
        G.add_edge(
            (l["source"], node_group_map[l["source"]]),
            (l["target"], node_group_map[l["target"]]), 
            weight=l["value"]
        )

    return G


def get_subclusters(G):
    nodes_seen = set()
    sub_clusters = []

    for n in G:
        if n in nodes_seen:
            continue

        cluster_num = n[1]

        unexplored_nodes = set()
        unexplored_nodes.add(n)

        sub_cluster = []

        while unexplored_nodes:
            curr_node = unexplored_nodes.pop()
            if curr_node[1] != cluster_num:
                continue

            nodes_seen.add(curr_node)
            sub_cluster.append(curr_node)

            for pre in G.predecessors(curr_node):
                if pre not in nodes_seen:
                    unexplored_nodes.add(pre)

            for post in G.successors(curr_node):
                if post not in nodes_seen:
                    unexplored_nodes.add(post)

        sub_clusters.append(sub_cluster)

    return sub_clusters


def get_subcluster_idx(subclusters, n):
    for i, s in enumerate(subclusters):
        for pair in s:
            if n == pair[0]:
                return i


def stats(G):
    print()
    
    subclusters = get_subclusters(G)
    counter = Counter([sc[0][1] for sc in subclusters])
    print("--- Cluster Summary ---")
    for cluster_n in counter:
        nodes = sum([len(sc) for sc in subclusters if sc[0][1] == cluster_n])
        print(str(cluster_n)+")", nodes, "nodes ["+str(counter[cluster_n])+" subcluster(s)]")
        for i, sc in enumerate(subclusters):
            if sc[0][1] != cluster_n:
                continue
            print("\tSub-cluster", str(i)+":", len(sc), "node(s)")
    print()

    counter = Counter([(e[0][1], e[1][1]) for e in G.edges() if e[0][1] != e[1][1]])
    print("--- Cluster Summary ---")
    print("Total cross-cluster edge(s):", sum(counter.values()))
    for e_count in counter:
        print("\t"+str(e_count[0])+" -> "+str(e_count[1])+":", counter[e_count], "edge(s)")
    print()

    counter = Counter([(get_subcluster_idx(subclusters, e[0][0]), get_subcluster_idx(subclusters, e[1][0])) for e in G.edges() if e[0][1] != e[1][1]])
    print("Total cross-sub-cluster edge(s):", sum(counter.values()))

    subcluster_G = nx.DiGraph()
    for i in range(len(subclusters)):
        subcluster_G.add_node(i)

    for e_count in counter:
        print("\t"+str(e_count[0])+" (cluster " + str(subclusters[e_count[0]][0][1]) + ") -> "+str(e_count[1])+" (cluster " + str(subclusters[e_count[1]][0][1]) + "):", counter[e_count], "edge(s)")
        subcluster_G.add_edge(e_count[0], e_count[1])

    print()
    try:
        path = nx.dag_longest_path(subcluster_G)
        print("Longest sub-cluster path:", path, "(length =", str(len(path))+")")
    except:
        print("Sub-cluster graph has cycles") 
    print()

    for i, sc in enumerate(subclusters):
        print("--- Sub-cluster", i, "Summary ---")

        cluster_num = sc[0][1]

        n_inputs = 0
        n_outputs = 0
        n_and, n_xor, n_inv = 0, 0, 0

        incoming_edges = []
        outgoing_edges = []

        for gate in sc:
            if "INPUT" in gate[0]:
                n_inputs += 1
            elif "OUTPUT" in gate[0]:
                n_outputs += 1
            elif "AND" in gate[0]:
                n_and += 1
            elif "XOR" in gate[0]:
                n_xor += 1
            elif "INV" in gate[0]:
                n_inv += 1

            for pre in G.predecessors(gate):
                if pre[1] != cluster_num:
                    incoming_edges.append((pre, get_subcluster_idx(subclusters, pre[0])))

            for post in G.successors(gate):
                if post[1] != cluster_num:
                    outgoing_edges.append((post, get_subcluster_idx(subclusters, post[0])))

        sc_view = nx.subgraph_view(G, filter_node = lambda n: n in sc)
        sc_depth = len(nx.dag_longest_path(sc_view))

        print("Input bits:", n_inputs)
        print("Incoming edges:", len(incoming_edges))
        for e in incoming_edges:
            print("    From", e[0][0], "| Sub-cluster", e[1], "(Cluster", str(e[0][1])+")")
        print("Gates:")
        print("    AND:", n_and)
        print("    XOR:", n_xor)
        print("    INV:", n_inv)
        print("Sub-cluster depth:", sc_depth)
        print("Output bits:", n_outputs)
        print("Outgoing edges:", len(outgoing_edges))
        for e in outgoing_edges:
            print("    To", e[0][0], "| Sub-cluster", e[1], "(Cluster", str(e[0][1])+")")
        print()


parser = argparse.ArgumentParser(description="Generate stats on partitioned graphs")
parser.add_argument("in_json_file", help="Path to input partitioned graph")

args = parser.parse_args()
with open(args.in_json_file, 'r') as f:
    graph = json.load(f)
G = to_networkx(graph)

stats(G)

