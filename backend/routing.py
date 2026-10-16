
from functools import lru_cache
from pathlib import Path

import networkx as nx
import osmnx as ox

GRAPH_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "nagpur_roads.graphml"
)


@lru_cache(maxsize=1)
def load_graph():
    if not GRAPH_FILE.exists():
        raise FileNotFoundError(
            f"Road graph not found: {GRAPH_FILE}"
        )

    return ox.load_graphml(GRAPH_FILE)


def calculate_route(start_lat, start_lon, end_lat, end_lon):
    graph = load_graph()

    start_node = ox.distance.nearest_nodes(
        graph, X=start_lon, Y=start_lat
    )
    end_node = ox.distance.nearest_nodes(
        graph, X=end_lon, Y=end_lat
    )

    try:
        route = nx.shortest_path(
            graph,
            source=start_node,
            target=end_node,
            weight="length",
        )
    except nx.NetworkXNoPath:
        raise ValueError(
            "No directed road route connects these locations."
        )

    coordinates = []
    distance_m = 0.0

    for node in route:
        data = graph.nodes[node]
        coordinates.append([data["y"], data["x"]])

    for u, v in zip(route[:-1], route[1:]):
        edges = graph.get_edge_data(u, v)
        distance_m += min(
            float(edge["length"])
            for edge in edges.values()
        )

    return {
        "start_node": start_node,
        "end_node": end_node,
        "distance_m": round(distance_m, 2),
        "distance_km": round(distance_m / 1000, 3),
        "route_nodes": len(route),
        "coordinates": coordinates,
        "weight": "road_distance_metres",
        "simulation": True,
    }
