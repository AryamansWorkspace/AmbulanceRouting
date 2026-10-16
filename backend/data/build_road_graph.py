
from pathlib import Path

import networkx as nx
import osmnx as ox

DATA_DIR = Path(__file__).resolve().parent
OSM_FILE = DATA_DIR / "planet_78.9622,21.0621_79.2178,21.2378.osm"
GRAPH_FILE = DATA_DIR / "nagpur_roads.graphml"

# Road types suitable for a basic ambulance-driving simulation.
DRIVABLE_ROADS = {
    "motorway", "motorway_link",
    "trunk", "trunk_link",
    "primary", "primary_link",
    "secondary", "secondary_link",
    "tertiary", "tertiary_link",
    "unclassified", "residential",
    "living_street", "service", "road",
}

RESTRICTED_ACCESS = {
    "no", "private", "agricultural", "forestry"
}


def main():
    if not OSM_FILE.exists():
        raise FileNotFoundError(f"OSM extract not found: {OSM_FILE}")

    print(f"Loading local OSM extract: {OSM_FILE}")
    print("No Overpass download will be performed.")

    graph = ox.graph_from_xml(
        OSM_FILE,
        simplify=False,
        retain_all=True,
        bidirectional=False,
    )

    print(f"Raw graph: {len(graph.nodes):,} nodes, "
          f"{len(graph.edges):,} edges")

    # Keep suitable roads and exclude explicitly restricted access.
    remove_edges = []

    for u, v, key, data in graph.edges(keys=True, data=True):
        highway = data.get("highway", [])
        if isinstance(highway, str):
            highway = [highway]

        allowed_road = any(
            road in DRIVABLE_ROADS for road in highway
        )

        restricted = any(
            str(data.get(tag, "")).lower() in RESTRICTED_ACCESS
            for tag in ("access", "vehicle", "motor_vehicle", "motorcar")
        )

        if not allowed_road or restricted:
            remove_edges.append((u, v, key))

    graph.remove_edges_from(remove_edges)
    graph.remove_nodes_from(list(nx.isolates(graph)))

    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        raise RuntimeError("No drivable roads remain after filtering.")

    # Calculate edge lengths in metres before simplifying.
    graph = ox.distance.add_edge_lengths(graph)
    graph = ox.simplification.simplify_graph(graph)

    # Save the local graph for subsequent routing operations.
    ox.save_graphml(graph, GRAPH_FILE)

    print("\nRoad graph saved successfully.")
    print(f"File: {GRAPH_FILE}")
    print(f"Nodes: {graph.number_of_nodes():,}")
    print(f"Edges: {graph.number_of_edges():,}")
    print("Edge weights: length (metres)")
    print("Source: local OpenStreetMap extract")


if __name__ == "__main__":
    main()
