
import math
import re

import networkx as nx
import osmnx as ox

from backend.routing import load_graph


def normalize_name(name):
    return re.sub(r"\s+", " ", str(name or "")).strip().casefold()


def is_suitable_candidate(name):
    name = normalize_name(name)
    excluded = ("optical", "eyewear", "spectacles", "pharmacy", "medical store")
    return not any(term in name for term in excluded)


def coordinates_are_close(first, second, threshold_m=150):
    lat = first["latitude"]
    distance = math.hypot(
        (lat - second["latitude"]) * 111_000,
        (first["longitude"] - second["longitude"])
        * 111_000 * math.cos(math.radians(lat)),
    )
    return distance <= threshold_m


def relevance_score(name, description="", category=""):
    """Estimate name relevance only; this does not verify medical capability."""
    text = normalize_name(f"{name} {description} {category}")
    score = 0
    reasons = []

    general_terms = (
        "multispeciality", "multi-speciality", "super speciality",
        "superspeciality", "general hospital", "medical college",
    )
    emergency_terms = ("emergency", "trauma", "critical care")
    cardiac_terms = ("cardiac", "cardiology", "heart")

    if any(term in text for term in general_terms):
        score += 2
        reasons.append("general-care name hint")

    if any(term in text for term in emergency_terms):
        score += 3
        reasons.append("emergency/trauma name hint")

    urgent_symptoms = any(
        term in text
        for term in ("chest pain", "breathing difficulty", "difficulty breathing",
                     "shortness of breath", "heart attack")
    )
    accident = any(
        term in text
        for term in ("road accident", "accident", "collision", "crash", "trauma")
    )

    if urgent_symptoms and any(term in text for term in cardiac_terms):
        score += 2
        reasons.append("cardiac name hint")

    if accident and any(
        term in text for term in ("trauma", "emergency", "surgical")
    ):
        score += 2
        reasons.append("trauma/surgical name hint")

    # Lower the priority of narrowly named facilities for unrelated emergencies.
    specialty_terms = (
        "eye hospital", "netralaya", "maternity", "children",
        "childrens", "orthopedic", "ortho hospital",
    )
    if (urgent_symptoms or accident) and any(
        term in normalize_name(name) for term in specialty_terms
    ):
        score -= 2
        reasons.append("specialty-specific name; capability unverified")

    return score, "; ".join(reasons) or "No clear name-based relevance hint"


def recommend_hospitals(
    latitude,
    longitude,
    hospitals,
    limit=5,
    emergency_description="",
    emergency_category="",
):
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

    graph = load_graph()
    start = ox.distance.nearest_nodes(graph, X=longitude, Y=latitude)
    distances = nx.single_source_dijkstra_path_length(
        graph, start, weight="length"
    )

    valid = []
    skipped = 0

    for hospital in hospitals:
        if not isinstance(hospital, dict):
            skipped += 1
            continue

        name = hospital.get("name") or "Unnamed candidate"
        lat, lon = hospital.get("latitude"), hospital.get("longitude")

        if (
            not is_suitable_candidate(name)
            or isinstance(lat, bool) or isinstance(lon, bool)
            or not isinstance(lat, (int, float))
            or not isinstance(lon, (int, float))
            or not math.isfinite(lat) or not math.isfinite(lon)
            or not -90 <= lat <= 90 or not -180 <= lon <= 180
        ):
            skipped += 1
            continue

        valid.append((hospital, name, lat, lon))

    if not valid:
        return {
            "recommendations": [],
            "skipped_candidates": skipped,
            "ranking_basis": "Estimated relevance, then road distance",
            "simulation": True,
        }

    nodes = ox.distance.nearest_nodes(
        graph,
        X=[item[3] for item in valid],
        Y=[item[2] for item in valid],
    )

    ranked = []
    for (hospital, name, lat, lon), node in zip(valid, nodes):
        if node not in distances:
            skipped += 1
            continue

        score, reason = relevance_score(
            name, emergency_description, emergency_category
        )
        ranked.append({
            "id": hospital.get("id"),
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "verified": hospital.get("verified", False),
            "road_distance_km": round(distances[node] / 1000, 3),
            "relevance_score": score,
            "relevance_hint": reason,
        })

    # Higher name-based relevance first; use road distance to break ties.
    ranked.sort(key=lambda item: (
        -item["relevance_score"], item["road_distance_km"]
    ))

    deduplicated = []
    seen = {}

    for candidate in ranked:
        key = normalize_name(candidate["name"])
        previous = seen.get(key, [])

        if any(coordinates_are_close(candidate, item) for item in previous):
            skipped += 1
            continue

        deduplicated.append(candidate)
        seen.setdefault(key, []).append(candidate)

    return {
        "recommendations": deduplicated[:limit],
        "skipped_candidates": skipped,
        "ranking_basis": "Unverified name-based relevance estimate, then calculated road distance",
        "simulation": True,
        "note": (
            "Name-based hints are not verified medical capabilities. "
            "Hospital suitability, emergency services and availability "
            "are not confirmed."
        ),
    }
