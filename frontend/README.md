# Ambulance Routing Frontend

This React/Vite frontend is the primary AmbulanceRouting dashboard with the
clean Clinivue visual style and Clinivue Firebase Google authentication.

## Local setup

```powershell
cd D:\MajorProject\AmbulanceRouting\frontend
npm ci
Copy-Item .env.example .env
```

Set `VITE_FIREBASE_API_KEY` in `.env` using the Clinivue Firebase Web API key.
The API key is intentionally not committed to Git.

Start the frontend after starting the backend:

```powershell
npm run dev
```

The dashboard is available at `http://localhost:5173`.

## Validation

```powershell
npm run lint
npm run build
```

The backend remains the primary ambulance-routing API and runs from the
repository root:

```powershell
cd ..
.\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
