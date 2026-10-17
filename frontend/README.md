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

After authentication, use the `Clinivue` navigation item to access the
integrated AI assistant, cost and provider insights, lab report analyzer, and
encrypted history. Those features require the secondary Clinivue service:

```powershell
cd D:\MajorProject\AmbulanceRouting\clinivue\backend
..\..\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

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
