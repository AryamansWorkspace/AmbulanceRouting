
from fastapi import FastAPI

app = FastAPI(
    title="Ambulance Routing API",
    description="Backend for the Ambulance Routing Digital Twin",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Ambulance Routing API is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
