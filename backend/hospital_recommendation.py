
import math

import networkx as nx
import osmnx as ox

from backend.routing import load_graph


def recommend_hospitals(latitude, longitude, hospitals, limit=5):
    if (
        isinstance(latitude, bool) or isinstance(longitude, bool)
        or not isinstance(latitude, (int, float))
        or not isinstance(longitude, (int, float))
        or not math.isfinite(latitude) or not math.isfinite(longitude)
        or not -90 <= latitude <= 90
        or not -180 <= longitude <= 180
    ):
        raise ValueError("Invalid emergency coordinates.")

    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("Limit must be a positive integer.")

    if not isinstance(hospitals, list):
        raise ValueError("Hospitals must be a list.")

    if not hospitals:
        return {"recommendations": [], "skipped_candidates": 0,
                "message": "No hospital candidates available."}

    graph = load_graph()
    start = ox.distance.nearest_nodes(
        graph, X=longitude, Y=latitude
    )
    distances = nx.single_source_dijkstra_path_length(
        graph, start, weight="length"
    )

    valid = []
    skipped = 0

    for hospital in hospitals:
        if not isinstance(hospital, dict):
            skipped += 1
            continue

        lat, lon = hospital.get("latitude"), hospital.get("longitude")
        if (
            isinstance(lat, bool) or isinstance(lon, bool)
            or not isinstance(lat, (int, float))
            or not isinstance(lon, (int, float))
            or not math.isfinite(lat) or not math.isfinite(lon)
            or not -90 <= lat <= 90 or not -180 <= lon <= 180
        ):
            skipped += 1
            continue

        valid.append((hospital, lat, lon))

    if not valid:
        return {
            "recommendations": [],
            "skipped_candidates": skipped,
            "message": "No candidates have valid coordinates.",
        }

    # Resolve all candidate coordinates in one OSMnx call.
    nodes = ox.distance.nearest_nodes(
        graph,
        X=[lon for _, _, lon in valid],
        Y=[lat for _, lat, _ in valid],
    )

    ranked = []
    for (hospital, lat, lon), node in zip(valid, nodes):
        if node not in distances:
            skipped += 1
            continue

        ranked.append({
            "id": hospital.get("id"),
            "name": hospital.get("name") or "Unnamed candidate",
            "latitude": lat,
            "longitude": lon,
            "verified": hospital.get("verified", False),
            "road_distance_km": round(distances[node] / 1000, 3),
            "reason": "Ranked by shortest calculated road distance; "
                      "operational status and availability are unverified.",
        })

    ranked.sort(key=lambda item: item["road_distance_km"])

    return {
        "recommendations": ranked[:limit],
        "skipped_candidates": skipped,
        "ranking_basis": "Shortest road distance in the local OSM graph",
        "simulation": True,
        "note": "Candidates are not confirmed operational hospitals. "
                "Road distance does not establish medical suitability "
                "or current availability.",
    }
