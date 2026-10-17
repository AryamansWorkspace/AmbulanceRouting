
from functools import lru_cache
from pathlib import Path

import networkx as nx
import osmnx as ox

from backend.traffic_simulation import (
    edge_coordinates,
    edge_time_seconds,
    is_blocked,
    road_status,
)

GRAPH_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "nagpur_roads.graphml"
)

ROUTE_SCENARIOS = {"baseline", "normal", "congested", "blockage"}


@lru_cache(maxsize=1)
def load_graph():
    if not GRAPH_FILE.exists():
        raise FileNotFoundError(
            f"Road graph not found: {GRAPH_FILE}"
        )
    return ox.load_graphml(GRAPH_FILE)


def calculate_route(
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    scenario="baseline",
):
    if scenario not in ROUTE_SCENARIOS:
        raise ValueError("Unsupported routing scenario.")

    graph = load_graph()

    start_node = ox.distance.nearest_nodes(
        graph, X=start_lon, Y=start_lat
    )
    end_node = ox.distance.nearest_nodes(
        graph, X=end_lon, Y=end_lat
    )

    routing_graph = graph

    if scenario == "blockage":
        routing_graph = nx.subgraph_view(
            graph,
            filter_edge=lambda u, v, key: not is_blocked(
                u, v, key
            ),
        )

    if scenario == "baseline":
        weight = "length"
    else:
        def weight(u, v, edge_data):
            options = (
                edge_data.values()
                if "length" not in edge_data
                else [edge_data]
            )

            if scenario == "blockage":
                options = [
                    attrs
                    for key, attrs in edge_data.items()
                    if not is_blocked(u, v, key)
                ]

            if not options:
                return float("inf")

            return min(
                edge_time_seconds(attrs, scenario)
                for attrs in options
            )

    try:
        route = nx.shortest_path(
            routing_graph,
            source=start_node,
            target=end_node,
            weight=weight,
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        raise ValueError(
            "No road route connects these locations "
            "under the selected scenario."
        )

    coordinates = [
        [graph.nodes[node]["y"], graph.nodes[node]["x"]]
        for node in route
    ]

    route_segments = []
    distance_m = 0.0
    estimated_seconds = 0.0

    for u, v in zip(route[:-1], route[1:]):
        edge_data = graph.get_edge_data(u, v)

        if not edge_data:
            continue

        candidates = list(edge_data.items())

        # Never select a blocked parallel edge for the displayed route.
        if scenario == "blockage":
            candidates = [
                (key, attrs)
                for key, attrs in candidates
                if not is_blocked(u, v, key)
            ]

        if not candidates:
            raise ValueError(
                "A route edge is unavailable under the selected scenario."
            )

        if scenario == "baseline":
            key, attrs = min(
                candidates,
                key=lambda item: float(
                    item[1].get("length", 1)
                ),
            )
        else:
            key, attrs = min(
                candidates,
                key=lambda item: edge_time_seconds(
                    item[1], scenario
                ),
            )

        length = max(0.0, float(attrs.get("length", 0)))
        distance_m += length

        if scenario != "baseline":
            estimated_seconds += edge_time_seconds(
                attrs, scenario
            )

            route_segments.append({
                "coordinates": edge_coordinates(
                    graph, u, v, attrs
                ),
                "status": road_status(
                    u, v, key, attrs, scenario
                ),
            })

    result = {
        "start_node": start_node,
        "end_node": end_node,
        "distance_m": round(distance_m, 2),
        "distance_km": round(distance_m / 1000, 3),
        "route_nodes": len(route),
        "coordinates": coordinates,
        "weight": (
            "road_distance_metres"
            if scenario == "baseline"
            else "ml_estimated_travel_time_seconds"
        ),
        "scenario": scenario,
        "simulation": True,
    }

    if scenario != "baseline":
        result["estimated_time_min"] = round(
            estimated_seconds / 60, 2
        )
        result["route_segments"] = route_segments
        result["traffic_model"] = (
            "Random Forest trained on synthetic traffic data"
        )

    return result
