import argparse
import json
import networkx as nx
from itertools import permutations 

def to_networkx(graph_json):
    G = nx.Graph()

    for n in graph["nodes"]:
        G.add_node(n["id"])

    for l in graph["links"]:
        G.add_edge(l["source"], l["target"], weight=l["value"])

    return G

def from_networkx(G):
    nodes = []
    for n in G:
        nodes.append({
            "id": n,
            "group": 0
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


def three_cut(G):
    G_best_cut = None

    # Phase 1
    w_star = float("inf")
    for v in sorted(G, key = lambda x: len(G[x].keys())):
        w_1 = sum(G[v][e]["weight"] for e in G[v])

        G_minus_v = G.copy()
        G_minus_v.remove_node(v)
        
        connected_components = nx.number_connected_components(G_minus_v)
        if connected_components == 1:
            edge_cut = nx.minimum_edge_cut(G_minus_v)
            w_2 = sum(G_minus_v[e[0]][e[1]]["weight"] for e in edge_cut)
        elif connected_components == 2:
            edge_cut = []
            w_2 = 0
        else:
            continue

        if w_1 + w_2 < w_star:
            w_star = w_1 + w_2

            # Save cut graph
            G_best_cut = G.copy()

            # V_1
            neighbor_edges = [e for e in G_best_cut[v]]
            for e in neighbor_edges:
                G_best_cut.remove_edge(v, e)

            # V_2 and V_2
            for e in edge_cut:
                G_best_cut.remove_edge(*e)

    # Phase 2
    perms = list(permutations(G.nodes, 4))
    for s_1, s_2, t_1, t_2 in perms:
        G_modified = G.copy()

        G_modified.add_node("s_infinite")
        G_modified.add_edge("s_infinite", s_1, weight=float("inf"))
        G_modified.add_edge("s_infinite", s_2, weight=float("inf"))

        G_modified.add_node("t_infinite")
        G_modified.add_edge("t_infinite", t_1, weight=float("inf"))
        G_modified.add_edge("t_infinite", t_2, weight=float("inf"))

        cut_value, partition = nx.minimum_cut(G_modified, "s_infinite", "t_infinite", capacity="weight")
        V_s, V_t = partition[0], partition[1]

        G_V_t = G.copy()
        remove_list = []
        for n in G_V_t:
            if n not in V_t:
                remove_list.append(n)
        for n in remove_list:
            G_V_t.remove_node(n)
        
        v_t_cut_value, second_partition = nx.minimum_cut(G_V_t, t_1, t_2, capacity="weight")
        V_t1, V_t2 = second_partition[0], second_partition[1]

        if cut_value + v_t_cut_value < w_star:
            w_star = cut_value + v_t_cut_value

            # Save cut graph
            G_best_cut = G.copy()
            for e in G_best_cut.edges():
                if (e[0] in V_s and e[1] in V_s) or (e[0] in V_t1 and e[1] in V_t1) or (e[0] in V_t2 and e[1] in V_t2):
                    continue
                G_best_cut.remove_edge(*e[:2])
        
    return G_best_cut
        

parser = argparse.ArgumentParser(description="Minimum k-cut graph algorithm (Goldschmidt and Hochbaum '94).")
parser.add_argument("in_json_file", help="Input file location")
parser.add_argument("out_json_file", help="Output file location")

args = parser.parse_args()

with open(args.in_json_file, 'r') as f:
    graph = json.load(f)

G = to_networkx(graph)

# k-cut
G_cut = three_cut(G)
output_graph = from_networkx(G_cut)

with open(args.out_json_file, 'w') as f:
    json.dump(output_graph, f)

