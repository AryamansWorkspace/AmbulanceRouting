from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Ambulance Routing API",
    description="Backend for the Ambulance Routing Digital Twin",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HOSPITALS_FILE = Path(__file__).resolve().parent / "data" / "hospitals.json"


@app.get("/")
def home():
    return {
        "message": "Ambulance Routing API is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/hospitals")
def get_hospitals():
    if not HOSPITALS_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="Hospital dataset file not found.",
        )

    try:
        with HOSPITALS_FILE.open("r", encoding="utf-8") as file:
            hospitals = json.load(file)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Hospital dataset contains invalid JSON.",
        )

    if not isinstance(hospitals, list):
        raise HTTPException(
            status_code=500,
            detail="Hospital dataset must contain a JSON list.",
        )

    return hospitals
