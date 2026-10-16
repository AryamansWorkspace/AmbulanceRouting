import { useEffect, useState } from "react";
import MapView from "./MapView";
import EmergencyForm from "./EmergencyForm";
import "./App.css";

const API = "http://127.0.0.1:8000";
const NAV = ["Dashboard", "Emergencies", "Ambulances", "Hospitals"];

export default function App() {
  const [page, setPage] = useState("Dashboard");
  const [emergencies, setEmergencies] = useState([]);
  const [ambulances, setAmbulances] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [search, setSearch] = useState("");
  const [online, setOnline] = useState(false);
  const [error, setError] = useState("");

  async function refreshData() {
    try {
      const [health, emergencyRes, ambulanceRes, hospitalRes] =
        await Promise.all([
          fetch(`${API}/health`),
          fetch(`${API}/emergencies`),
          fetch(`${API}/ambulances`),
          fetch(`${API}/hospitals`),
        ]);

      if (![health, emergencyRes, ambulanceRes, hospitalRes].every(r => r.ok)) {
        throw Error("Some backend services are unavailable.");
      }

      const [h, e, a, hospitalsData] = await Promise.all([
        health.json(),
        emergencyRes.json(),
        ambulanceRes.json(),
        hospitalRes.json(),
      ]);

      setOnline(Boolean(h));
      setEmergencies(Array.isArray(e) ? e : e.emergencies || []);
      setAmbulances(Array.isArray(a) ? a : a.ambulances || []);
      setHospitals(
        Array.isArray(hospitalsData)
          ? hospitalsData
          : hospitalsData.hospitals || []
      );
      setError("");
    } catch {
      setOnline(false);
      setError("Backend unavailable. Check that the FastAPI server is running.");
    }
  }

  useEffect(() => {
    refreshData();
    const timer = setInterval(refreshData, 15000);
    return () => clearInterval(timer);
  }, []);

  const filteredHospitals = hospitals.filter(h =>
    (h.name || "").toLowerCase().includes(search.toLowerCase())
  );

  const records = {
    Emergencies: emergencies,
    Ambulances: ambulances,
    Hospitals: filteredHospitals,
  }[page] || [];

  function renderRecords() {
    return (
      <>
        {page === "Emergencies" && (
          <EmergencyForm onReported={refreshData} />
        )}

        {page === "Hospitals" && (
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search hospitals..."
            className="search-input"
          />
        )}

        <section className="panel panel-body">
          <h3>
            {page === "Emergencies"
              ? "Reported Emergencies"
              : page === "Ambulances"
              ? "Ambulance Fleet"
              : "Hospital Directory"}
          </h3>

          {!records.length ? (
            <p>No records available.</p>
          ) : (
            records.slice(0, 100).map((item, i) => (
              <div className="incident" key={item.id ?? item.name ?? i}>
                <div className="incident-title">
                  {page === "Hospitals"
                    ? "🏥 "
                    : page === "Ambulances"
                    ? "🚑 "
                    : "🚨 "}
                  {item.name || `#${item.id} · ${item.category || "Record"}`}
                </div>
                <p className="incident-description">
                  {item.description || item.status || item.category ||
                    "Hospital candidate"}
                </p>
                <span className="small-label">
                  Status: {item.status || "Unverified"} · Location:{" "}
                  {item.latitude ?? "—"}, {item.longitude ?? "—"}
                </span>
              </div>
            ))
          )}
        </section>
      </>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <strong>🚑 Emergency Management Digital Twin</strong>
          <div className="small-label">Nagpur · Simulation Dashboard</div>
        </div>
        <span className="small-label">
          {online ? "🟢 Backend Online" : "🔴 Backend Offline"}
        </span>
      </header>

      <div className="app-layout">
        <aside className="sidebar">
          <h3>Navigation</h3>
          {NAV.map(item => (
            <button
              key={item}
              className={page === item ? "nav-item active" : "nav-item"}
              onClick={() => setPage(item)}
            >
              {item}
            </button>
          ))}
        </aside>

        <main className="main-content">
          <h2>{page}</h2>
          {error && <p role="alert">{error}</p>}

          {page === "Dashboard" ? (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <span>Active Emergencies</span>
                  <h2>{emergencies.filter(e =>
                    !["resolved", "completed", "closed"].includes(
                      (e.status || "").toLowerCase()
                    )
                  ).length}</h2>
                </div>
                <div className="stat-card">
                  <span>Ambulances Available</span>
                  <h2>{ambulances.filter(a =>
                    (a.status || "").toLowerCase() === "available"
                  ).length}</h2>
                </div>
                <div className="stat-card">
                  <span>Hospital Candidates</span>
                  <h2>{hospitals.length}</h2>
                </div>
                <div className="stat-card">
                  <span>Routes Calculated</span>
                  <h2>—</h2>
                </div>
              </div>

              <section className="panel panel-body">
                <h3>Nagpur Emergency Map</h3>
                <MapView />
              </section>

              <section className="panel panel-body">
                <h3>Recent Emergencies</h3>
                {!emergencies.length ? (
                  <p>No emergencies reported yet.</p>
                ) : (
                  emergencies.slice(0, 5).map((item, i) => (
                    <div className="incident" key={item.id ?? i}>
                      <div className="incident-title">
                        🚨 {item.category || `Emergency #${item.id}`}
                      </div>
                      <p className="incident-description">
                        {item.description}
                      </p>
                      <span className="small-label">
                        Status: {item.status || "Reported"}
                      </span>
                    </div>
                  ))
                )}
              </section>
            </>
          ) : (
            renderRecords()
          )}

          <footer className="footer">
            Academic proof of concept. Emergency data, ambulance operations,
            and availability are simulated or unverified where indicated.
          </footer>
        </main>
      </div>
    </div>
  );
}