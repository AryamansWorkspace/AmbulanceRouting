# Clinivue feature service

Clinivue is integrated as a secondary service and feature area. The
AmbulanceRouting backend remains the primary API on port `8000`. Clinivue runs
independently on port `8001`, while the unified frontend exposes it from the
`Clinivue` navigation item.

## Backend setup

```powershell
cd D:\MajorProject\AmbulanceRouting
.\backend\.venv\Scripts\python.exe -m pip install -r clinivue\backend\requirements.txt
Copy-Item clinivue\backend\.env.example clinivue\backend\.env
```

Set the AI and OCR provider keys in `clinivue\backend\.env` as needed, then
start the service:

```powershell
cd D:\MajorProject\AmbulanceRouting\clinivue\backend
..\..\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Clinivue API documentation is available at
`http://127.0.0.1:8001/docs`.

The frontend also needs `VITE_FIREBASE_API_KEY` and
`VITE_CLINIVUE_API_URL=http://127.0.0.1:8001` in `frontend\.env`.

## Frontend

Start the primary frontend from `frontend`:

```powershell
npm run dev
```

After signing in, choose `Clinivue` in the navigation to access AI chat,
provider and cost insights, lab report analysis, and encrypted history.
