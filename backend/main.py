
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.database import get_connection, init_db
from backend.emergency_nlp import categorize_emergency
from backend.hospital_recommendation import recommend_hospitals
from backend.routing import calculate_route

HOSPITALS_FILE = Path(__file__).resolve().parent / "data" / "hospitals.json"

app = FastAPI(
    title="Ambulance Routing API",
    description="Backend for the Ambulance Routing Digital Twin",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HospitalRecommendationRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    limit: int = Field(default=5, ge=1, le=20)


class EmergencyRequest(BaseModel):
    description: str = Field(min_length=1, max_length=1000)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


@app.get("/")
def home():
    return {"message": "Ambulance Routing API is running", "status": "success"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/hospitals")
def get_hospitals():
    if not HOSPITALS_FILE.exists():
        raise HTTPException(status_code=500, detail="Hospital dataset file not found.")

    try:
        with HOSPITALS_FILE.open("r", encoding="utf-8") as file:
            hospitals = json.load(file)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Hospital dataset contains invalid JSON.")

    if not isinstance(hospitals, list):
        raise HTTPException(status_code=500, detail="Hospital dataset must contain a JSON list.")

    return hospitals


@app.get("/route")
def get_route(
    start_lat: float = Query(..., ge=-90, le=90),
    start_lon: float = Query(..., ge=-180, le=180),
    end_lat: float = Query(..., ge=-90, le=90),
    end_lon: float = Query(..., ge=-180, le=180),
):
    try:
        return calculate_route(start_lat, start_lon, end_lat, end_lon)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/recommend-hospitals")
def get_hospital_recommendations(request: HospitalRecommendationRequest):
    if not HOSPITALS_FILE.exists():
        raise HTTPException(status_code=500, detail="Hospital dataset file not found.")

    try:
        with HOSPITALS_FILE.open("r", encoding="utf-8") as file:
            hospitals = json.load(file)

        if not isinstance(hospitals, list):
            raise HTTPException(status_code=500, detail="Hospital dataset must contain a JSON list.")

        return recommend_hospitals(
            request.latitude, request.longitude, hospitals, request.limit
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Hospital dataset contains invalid JSON.")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/emergencies", status_code=201)
def create_emergency(request: EmergencyRequest):
    description = request.description.strip()
    if not description:
        raise HTTPException(status_code=422, detail="Enter an emergency description.")

    try:
        result = categorize_emergency(description)
        init_db()

        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO emergencies
                    (description, latitude, longitude, category, confidence)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    description,
                    request.latitude,
                    request.longitude,
                    result["category"],
                    result["confidence"],
                ),
            )
            emergency_id = cursor.lastrowid

        return {
            "id": emergency_id,
            "description": description,
            "latitude": request.latitude,
            "longitude": request.longitude,
            **result,
            "status": "reported",
            "simulation": True,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to save emergency report.") from exc

@app.get("/emergencies")
def get_emergencies(limit: int = Query(default=50, ge=1, le=200)):
    init_db()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, description, latitude, longitude,
                   category, confidence, status, created_at
            FROM emergencies
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]