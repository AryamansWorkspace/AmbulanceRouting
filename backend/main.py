
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.database import get_connection, init_db
from backend.routing import calculate_route
from backend.hospital_recommendation import recommend_hospitals
from backend.emergency_nlp import categorize_emergency

app = FastAPI(title="Ambulance Routing Digital Twin")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HOSPITALS_FILE = Path(__file__).resolve().parent / "data" / "hospitals.json"


class EmergencyRequest(BaseModel):
    description: str = Field(min_length=3, max_length=500)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class HospitalRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    limit: int = Field(default=5, ge=1, le=20)
    description: str = Field(default="", max_length=500)
    category: str = Field(default="", max_length=100)


class DispatchRequest(BaseModel):
    emergency_id: int = Field(gt=0)
    ambulance_id: int = Field(gt=0)
    hospital_id: str = Field(min_length=1, max_length=100)


def hospitals():
    try:
        data = json.loads(HOSPITALS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Hospital data must be a list.")
        return data
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(500, f"Hospital data error: {exc}")


def route_or_error(*coords):
    try:
        return calculate_route(*coords)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except FileNotFoundError:
        raise HTTPException(500, "Road network graph not found.")


def recommend_for_emergency(emergency, limit=5):
    return recommend_hospitals(
        emergency["latitude"],
        emergency["longitude"],
        hospitals(),
        limit,
        emergency.get("description", ""),
        emergency.get("category", ""),
    )


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home():
    return {
        "message": "Ambulance Routing Digital Twin API",
        "simulation": True,
    }


@app.get("/health")
def health():
    return {"status": "ok", "simulation": True}


@app.get("/geocode")
def geocode_location(q: str = Query(..., min_length=3, max_length=200)):
    """Find possible locations in Nagpur using OpenStreetMap Nominatim."""
    params = urlencode({
        "q": f"{q}, Nagpur, Maharashtra, India",
        "format": "jsonv2",
        "limit": 3,
        "countrycodes": "in",
    })

    request = Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": "AmbulanceRoutingAcademicPOC/1.0"},
    )

    try:
        with urlopen(request, timeout=10) as response:
            results = json.loads(response.read().decode("utf-8"))

        return {
            "results": [
                {
                    "name": item["display_name"],
                    "latitude": float(item["lat"]),
                    "longitude": float(item["lon"]),
                }
                for item in results
            ],
            "simulation": True,
        }
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        raise HTTPException(
            502,
            "Location search is temporarily unavailable. Please try again.",
        )


@app.get("/hospitals")
def get_hospitals():
    return hospitals()


@app.get("/route")
def get_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
):
    return route_or_error(start_lat, start_lon, end_lat, end_lon)


@app.post("/recommend-hospitals")
def get_recommendations(request: HospitalRequest):
    return recommend_hospitals(
        request.latitude,
        request.longitude,
        hospitals(),
        request.limit,
        request.description,
        request.category,
    )


@app.post("/emergencies", status_code=201)
def create_emergency(request: EmergencyRequest):
    result = categorize_emergency(request.description)

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO emergencies
            (description, latitude, longitude, category, confidence)
            VALUES (?, ?, ?, ?, ?)""",
            (
                request.description,
                request.latitude,
                request.longitude,
                result["category"],
                result.get("confidence"),
            ),
        )
        emergency_id = cursor.lastrowid

    return {
        "id": emergency_id,
        **request.model_dump(),
        **result,
        "status": "reported",
        "simulation": True,
    }


@app.get("/emergencies")
def get_emergencies():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM emergencies ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/ambulances")
def get_ambulances():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM ambulances ORDER BY id"
        ).fetchall()

    return {
        "ambulances": [dict(row) for row in rows],
        "simulation": True,
    }


@app.post("/dispatches", status_code=201)
def create_dispatch(request: DispatchRequest):
    with get_connection() as conn:
        emergency = conn.execute(
            "SELECT * FROM emergencies WHERE id = ?",
            (request.emergency_id,),
        ).fetchone()
        ambulance = conn.execute(
            "SELECT * FROM ambulances WHERE id = ?",
            (request.ambulance_id,),
        ).fetchone()

    if not emergency:
        raise HTTPException(404, "Emergency not found.")
    if not ambulance:
        raise HTTPException(404, "Ambulance not found.")
    if emergency["status"] != "reported":
        raise HTTPException(409, "Emergency is not awaiting dispatch.")
    if ambulance["status"] != "available":
        raise HTTPException(409, "Ambulance is not available.")

    candidates = recommend_for_emergency(dict(emergency), limit=20)[
        "recommendations"
    ]

    hospital = next(
        (item for item in candidates
         if str(item.get("id")) == request.hospital_id),
        None,
    )

    if not hospital:
        raise HTTPException(
            422, "Hospital is not in the recommended list."
        )

    route = route_or_error(
        ambulance["latitude"],
        ambulance["longitude"],
        emergency["latitude"],
        emergency["longitude"],
    )

    try:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")

            current = conn.execute(
                "SELECT status FROM emergencies WHERE id = ?",
                (request.emergency_id,),
            ).fetchone()
            unit = conn.execute(
                "SELECT status FROM ambulances WHERE id = ?",
                (request.ambulance_id,),
            ).fetchone()

            if not current or current["status"] != "reported":
                raise HTTPException(409, "Emergency already dispatched.")
            if not unit or unit["status"] != "available":
                raise HTTPException(
                    409, "Ambulance is no longer available."
                )

            cursor = conn.execute(
                """INSERT INTO dispatches
                (emergency_id, ambulance_id, hospital_id)
                VALUES (?, ?, ?)""",
                (
                    request.emergency_id,
                    request.ambulance_id,
                    request.hospital_id,
                ),
            )

            conn.execute(
                "UPDATE emergencies SET status = 'dispatched' WHERE id = ?",
                (request.emergency_id,),
            )
            conn.execute(
                "UPDATE ambulances SET status = 'assigned' WHERE id = ?",
                (request.ambulance_id,),
            )

    except sqlite3.Error as exc:
        raise HTTPException(500, f"Dispatch database error: {exc}")

    return {
        "dispatch_id": cursor.lastrowid,
        "emergency_id": request.emergency_id,
        "ambulance_id": request.ambulance_id,
        "ambulance": ambulance["name"],
        "hospital": hospital,
        "status": "assigned",
        "route": route,
        "simulation": True,
    }


@app.get("/dispatches")
def get_dispatches():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT d.*, e.description, e.latitude, e.longitude,
                   a.name AS ambulance_name
            FROM dispatches d
            JOIN emergencies e ON e.id = d.emergency_id
            LEFT JOIN ambulances a ON a.id = d.ambulance_id
            ORDER BY d.id DESC
        """).fetchall()

    return {
        "dispatches": [dict(row) for row in rows],
        "simulation": True,
    }
