import random

from sklearn.ensemble import RandomForestRegressor


ROAD_CLASSES = {
    "motorway": 0,
    "trunk": 0,
    "primary": 1,
    "secondary": 2,
    "tertiary": 3,
    "residential": 4,
    "service": 5,
    "unclassified": 5,
}

BASE_SPEEDS = [65, 55, 45, 35, 25, 20]
CONGESTION_FACTORS = [0.95, 0.75, 0.48, 0.30]


def road_class_code(attrs):
    road_type = attrs.get("highway", "residential")
    if isinstance(road_type, (list, tuple)):
        road_type = road_type[0] if road_type else "residential"
    return ROAD_CLASSES.get(str(road_type).lower(), 4)


def stable_number(u, v, key=0):
    """Deterministic edge identifier for repeatable simulations."""
    text = f"{u}:{v}:{key}"
    return sum(
        (i + 1) * ord(char)
        for i, char in enumerate(text)
    ) % 1009


def is_blocked(u, v, key=0):
    """Simulated closures; unchanged between repeated runs."""
    return stable_number(u, v, key) % 23 == 0


def train_speed_model():
    """Train a Random Forest on synthetic traffic examples."""
    rng = random.Random(42)
    features, targets = [], []

    for road_class, base_speed in enumerate(BASE_SPEEDS):
        for hour in range(24):
            peak_factor = (
                0.78 if hour in list(range(7, 11))
                + list(range(17, 21)) else 1.0
            )

            for congestion in range(4):
                for incident in range(2):
                    for _ in range(4):
                        speed = (
                            base_speed
                            * CONGESTION_FACTORS[congestion]
                            * peak_factor
                            * (0.80 if incident else 1.0)
                            + rng.uniform(-3, 3)
                        )
                        features.append([
                            road_class, hour, congestion, incident
                        ])
                        targets.append(max(6, min(65, speed)))

    model = RandomForestRegressor(
        n_estimators=60,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(features, targets)
    return model


SPEED_MODEL = train_speed_model()


def scenario_inputs(scenario):
    if scenario == "normal":
        return 0, 0
    if scenario == "congested":
        return 2, 0
    if scenario == "blockage":
        return 2, 1
    raise ValueError("Unsupported traffic scenario.")


def estimate_speed_kmh(attrs, scenario, hour=8):
    congestion, incident = scenario_inputs(scenario)
    prediction = SPEED_MODEL.predict([[
        road_class_code(attrs), hour, congestion, incident
    ]])[0]
    return max(6.0, min(65.0, float(prediction)))


def edge_time_seconds(attrs, scenario):
    speed = estimate_speed_kmh(attrs, scenario)
    length = max(1.0, float(attrs.get("length", 1.0)))
    return length / (speed * 1000 / 3600)


def road_status(u, v, key, attrs, scenario):
    if scenario == "blockage" and is_blocked(u, v, key):
        return "blocked"

    speed = estimate_speed_kmh(attrs, scenario)
    if speed < 15:
        return "heavy"
    if speed < 27:
        return "moderate"
    return "free"


def edge_coordinates(graph, u, v, attrs):
    geometry = attrs.get("geometry")

    if geometry is not None:
        try:
            return [
                [lat, lon]
                for lon, lat, *_ in geometry.coords
            ]
        except (AttributeError, TypeError, ValueError):
            pass

    start = graph.nodes[u]
    end = graph.nodes[v]
    return [
        [start["y"], start["x"]],
        [end["y"], end["x"]],
    ]


def get_traffic_segments(graph, scenario, limit=180):
    """Return a repeatable sample of road segments for map display."""
    segments = []

    for u, v, key, attrs in graph.edges(
        keys=True, data=True
    ):
        signature = stable_number(u, v, key)

        # Sample the graph instead of drawing every road edge.
        if signature not in (0, 907):
            continue

        status = road_status(u, v, key, attrs, scenario)
        segments.append({
            "id": f"{u}-{v}-{key}",
            "coordinates": edge_coordinates(graph, u, v, attrs),
            "status": status,
            "speed_kmh": round(
                estimate_speed_kmh(attrs, scenario), 1
            ),
        })

        if len(segments) >= limit:
            break

    return {
        "scenario": scenario,
        "model": "Random Forest trained on synthetic traffic data",
        "simulation": True,
        "segments": segments,
    }