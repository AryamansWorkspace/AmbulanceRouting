import json
import csv
import hashlib
import re
from collections import Counter
from pathlib import Path

# Paths relative to this script
DATA_DIR = Path(__file__).resolve().parent
INPUT_FILE = DATA_DIR / "nagpur_hospitals.geojson"
OUTPUT_FILE = DATA_DIR / "hospitals.json"
REVIEW_FILE = DATA_DIR / "hospital_data_review.csv"


def get_record_id(feature, properties, coordinates):
    """Create a stable ID using the source ID or a deterministic fallback."""
    source_id = (
        feature.get("id")
        or properties.get("@id")
        or properties.get("osm_id")
        or properties.get("id")
    )

    if source_id is not None:
        return str(source_id)

    raw = json.dumps(
        [properties, coordinates],
        sort_keys=True,
        ensure_ascii=False
    )
    return "generated_" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def normalise_name(name):
    """Normalise names for duplicate detection."""
    return re.sub(r"\s+", " ", str(name)).strip().casefold()


def main():
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        return

    # Read the original file without modifying it.
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        geojson = json.load(file)

    if (
        not isinstance(geojson, dict)
        or geojson.get("type") != "FeatureCollection"
        or not isinstance(geojson.get("features"), list)
    ):
        print("ERROR: Invalid GeoJSON FeatureCollection structure.")
        return

    hospitals = []
    review_records = []
    candidates = []
    total_features = len(geojson["features"])

    def add_review(feature_id, name, reason, action):
        review_records.append({
            "source_id": feature_id,
            "name": name,
            "reason": reason,
            "action": action,
        })

    # First pass: validate and identify hospital candidates.
    for index, feature in enumerate(geojson["features"]):
        if not isinstance(feature, dict):
            add_review(index, "", "Feature is not a JSON object", "Excluded")
            continue

        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        name = str(properties.get("name") or "").strip()
        coordinates = geometry.get("coordinates")
        feature_id = get_record_id(feature, properties, coordinates)

        if geometry.get("type") != "Point":
            add_review(
                feature_id, name,
                "Geometry is missing or is not a Point",
                "Excluded"
            )
            continue

        if (
            not isinstance(coordinates, list)
            or len(coordinates) < 2
            or isinstance(coordinates[0], bool)
            or isinstance(coordinates[1], bool)
            or not isinstance(coordinates[0], (int, float))
            or not isinstance(coordinates[1], (int, float))
        ):
            add_review(
                feature_id, name,
                "Coordinates are missing or invalid",
                "Excluded"
            )
            continue

        longitude, latitude = coordinates[:2]

        if not (
            -180 <= longitude <= 180
            and -90 <= latitude <= 90
        ):
            add_review(
                feature_id, name,
                "Coordinates are outside valid geographic ranges",
                "Excluded"
            )
            continue

        tags = properties
        amenity = str(tags.get("amenity") or "").strip().lower()
        healthcare = str(tags.get("healthcare") or "").strip().lower()

        # Keep clinics out of the hospital dataset.
        if amenity == "clinic" or healthcare == "clinic":
            add_review(
                feature_id, name,
                "Tagged as a clinic rather than a hospital",
                "Excluded"
            )
            continue

        if amenity != "hospital" and healthcare != "hospital":
            add_review(
                feature_id, name,
                "No amenity=hospital or healthcare=hospital tag",
                "Excluded"
            )
            continue

        flags = []

        if not name:
            flags.append("Missing hospital name")

        if name.casefold() == "proposed site":
            flags.append("Name indicates a proposed site")

        # Retain the candidate for duplicate-name checking.
        candidates.append({
            "id": feature_id,
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "category": "hospital",
            "source": "OpenStreetMap",
            "verified": False,
            "_flags": flags,
            "_properties": tags,
        })

    # Second pass: identify repeated names without deleting records.
    name_counts = Counter(
        normalise_name(item["name"])
        for item in candidates
        if item["name"]
    )

    for item in candidates:
        flags = item["_flags"]
        name = item["name"]

        if name and name_counts[normalise_name(name)] > 1:
            flags.append("Repeated hospital name; location needs review")

        if not item["_properties"].get("amenity") or not item["_properties"].get("healthcare"):
            flags.append("One or more common healthcare tags are missing")

        # Unnamed records and proposed sites require review before display.
        exclude = (
            not name
            or name.casefold() == "proposed site"
        )

        if exclude:
            add_review(
                item["id"],
                name,
                "; ".join(flags),
                "Excluded pending manual review"
            )
            continue

        # Keep other records, even when their names repeat.
        hospitals.append({
            key: value
            for key, value in item.items()
            if not key.startswith("_")
        })

        if flags:
            add_review(
                item["id"],
                name,
                "; ".join(flags),
                "Retained; review recommended"
            )

    # Write the clean, frontend-friendly dataset.
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(hospitals, file, indent=2, ensure_ascii=False)

    # Write excluded and flagged records to the review report.
    with REVIEW_FILE.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["source_id", "name", "reason", "action"]
        )
        writer.writeheader()
        writer.writerows(review_records)

    excluded_count = sum(
        record["action"].startswith("Excluded")
        for record in review_records
    )
    flagged_count = sum(
        record["action"].startswith("Retained")
        for record in review_records
    )

    print("\nHospital data cleaning completed.")
    print(f"Input features: {total_features}")
    print(f"Retained hospitals: {len(hospitals)}")
    print(f"Excluded records: {excluded_count}")
    print(f"Retained records flagged for review: {flagged_count}")
    print(f"Review CSV rows: {len(review_records)}")
    print(f"\nClean dataset: {OUTPUT_FILE}")
    print(f"Review report: {REVIEW_FILE}")
    print("\nAll retained records have verified=False.")


if __name__ == "__main__":
    main()