import json

import networkx as nx


def get_cycles(g: nx.DiGraph) -> None:
    cycles = list(nx.simple_cycles(g))
    for cycle in cycles:
        for node in cycle:
            print("\t {}: {}".format(node, [str(x) for x in g.out_edges(node)]))


if __name__ == "__main__":
    """Extract edges from file and output a json file containing the device graph"""
    g = nx.DiGraph()
    with open("edges.txt") as f:
        for line in f.readlines():
            device, pred = line.strip().split(",")
            g.add_edge(pred, device)

    data = nx.node_link_data(g)
    with open("graph.json", "w") as f:
        f.write(json.dumps(data))
