
from pathlib import Path

import networkx as nx
import osmnx as ox

DATA_DIR = Path(__file__).resolve().parent
GRAPH_FILE = DATA_DIR / "nagpur_roads.graphml"

# Approximate coordinates: Zero Mile and Deekshabhoomi, Nagpur.
START = (21.1458, 79.0882)  # latitude, longitude
END = (21.1189, 79.0806)    # latitude, longitude


def main():
    print("Loading saved road graph...")
    graph = ox.load_graphml(GRAPH_FILE)

    # OSMnx expects longitude as X and latitude as Y.
    start_node = ox.distance.nearest_nodes(
        graph, X=START[1], Y=START[0]
    )
    end_node = ox.distance.nearest_nodes(
        graph, X=END[1], Y=END[0]
    )

    print(f"Start road node: {start_node}")
    print(f"End road node: {end_node}")

    try:
        route = nx.shortest_path(
            graph,
            source=start_node,
            target=end_node,
            weight="length",
        )
    except nx.NetworkXNoPath:
        print("No directed road path exists between these nodes.")
        return

    # Sum the shortest parallel-edge length for each route segment.
    distance_m = 0.0
    route_coordinates = []

    for node in route:
        data = graph.nodes[node]
        route_coordinates.append([data["y"], data["x"]])

    for u, v in zip(route[:-1], route[1:]):
        edges = graph.get_edge_data(u, v)
        distance_m += min(
            float(edge["length"]) for edge in edges.values()
        )

    print("\nROUTING TEST PASSED")
    print(f"Route nodes: {len(route)}")
    print(f"Road distance: {distance_m / 1000:.2f} km")
    print(f"Route coordinates: {len(route_coordinates)}")
    print("First coordinate [lat, lon]:", route_coordinates[0])
    print("Last coordinate [lat, lon]:", route_coordinates[-1])
    print("Weight: road distance in metres")


if __name__ == "__main__":
    main()
