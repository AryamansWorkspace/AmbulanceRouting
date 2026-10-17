
import { useEffect, useState } from "react";
import MapView from "./MapView";
import EmergencyForm from "./EmergencyForm";
import { logOut, onAuthChange } from "./lib/firebase";
import LoginPage from "./LoginPage";
import "./App.css";

const API = "http://127.0.0.1:8000";
const NAV = ["Dashboard", "Emergencies", "Ambulances", "Hospitals", "Dispatches"];

const AMBULANCE_STATUSES = [
  { value: "available", label: "Available" },
  { value: "assigned", label: "Busy / Assigned" },
  { value: "maintenance", label: "Maintenance" },
  { value: "offline", label: "Offline" },
];

const getList = (data, key) =>
  Array.isArray(data) ? data : data?.[key] || [];

const getStatusLabel = (status) => {
  const labels = {
    available: "Available",
    assigned: "Busy / Assigned",
    maintenance: "Maintenance",
    offline: "Offline",
  };
  return labels[(status || "").toLowerCase()] || status || "Unknown";
};

const getStatusStyle = (status) => {
  const styles = {
    available: { background: "#dcfce7", color: "#166534" },
    assigned: { background: "#fee2e2", color: "#991b1b" },
    maintenance: { background: "#fef3c7", color: "#92400e" },
    offline: { background: "#e5e7eb", color: "#374151" },
  };
  return styles[(status || "").toLowerCase()] || styles.offline;
};

function DashboardApp({ user }) {
  const [page, setPage] = useState("Dashboard");
  const [emergencies, setEmergencies] = useState([]);
  const [ambulances, setAmbulances] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [dispatches, setDispatches] = useState([]);
  const [search, setSearch] = useState("");
  const [online, setOnline] = useState(false);
  const [error, setError] = useState("");

  const [selectedEmergency, setSelectedEmergency] = useState("");
  const [selectedAmbulance, setSelectedAmbulance] = useState("");
  const [selectedHospital, setSelectedHospital] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [route, setRoute] = useState(null);
  const [dispatchError, setDispatchError] = useState("");
  const [dispatchMessage, setDispatchMessage] = useState("");
  const [loadingHospitals, setLoadingHospitals] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // NEW: Track ambulance status update progress and messages.
  const [updatingAmbulanceId, setUpdatingAmbulanceId] = useState(null);
  const [ambulanceStatusError, setAmbulanceStatusError] = useState("");
  const [ambulanceStatusMessage, setAmbulanceStatusMessage] = useState("");

  async function refreshData() {
    try {
      const endpoints = [
        "health", "emergencies", "ambulances", "hospitals", "dispatches",
      ];

      const responses = await Promise.all(
        endpoints.map((endpoint) => fetch(`${API}/${endpoint}`))
      );

      if (!responses.every((response) => response.ok)) {
        throw new Error("Backend services unavailable.");
      }

      const [health, e, a, h, d] = await Promise.all(
        responses.map((response) => response.json())
      );

      setOnline(Boolean(health));
      setEmergencies(getList(e, "emergencies"));
      setAmbulances(getList(a, "ambulances"));
      setHospitals(getList(h, "hospitals"));
      setDispatches(getList(d, "dispatches"));
      setError("");
    } catch {
      setOnline(false);
      setError("Backend unavailable. Check that the FastAPI server is running.");
    }
  }

  useEffect(() => {
    const initialRefresh = setTimeout(refreshData, 0);
    const timer = setInterval(refreshData, 15000);
    return () => {
      clearTimeout(initialRefresh);
      clearInterval(timer);
    };
  }, []);

  const activeEmergencies = emergencies.filter(
    (item) =>
      !["resolved", "completed", "closed"].includes(
        (item.status || "").toLowerCase()
      )
  );

  const availableAmbulances = ambulances.filter(
    (item) => (item.status || "").toLowerCase() === "available"
  );

  const busyAmbulances = ambulances.filter(
    (item) => (item.status || "").toLowerCase() === "assigned"
  );

  const unavailableAmbulances = ambulances.filter(
    (item) =>
      ["maintenance", "offline"].includes(
        (item.status || "").toLowerCase()
      )
  );

  const filteredHospitals = hospitals.filter((item) =>
    (item.name || "").toLowerCase().includes(search.toLowerCase())
  );

  // NEW: Save a status change through the backend API.
  async function updateAmbulanceStatus(ambulanceId, newStatus) {
    const ambulance = ambulances.find(
      (item) => item.id === ambulanceId
    );

    if (!ambulance || ambulance.status === newStatus) return;

    // Warn before making an assigned ambulance available again.
    if (
      ambulance.status === "assigned" &&
      newStatus === "available" &&
      !window.confirm(
        "This ambulance is currently assigned to a dispatch. " +
        "Only mark it available if the simulated assignment has ended."
      )
    ) {
      return;
    }

    setUpdatingAmbulanceId(ambulanceId);
    setAmbulanceStatusError("");
    setAmbulanceStatusMessage("");

    try {
      const response = await fetch(
        `${API}/ambulances/${ambulanceId}/status`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: newStatus }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not update ambulance status.");
      }

      setAmbulanceStatusMessage(
        `${data.name}: status changed to ${getStatusLabel(data.status)}.`
      );

      await refreshData();
    } catch (err) {
      setAmbulanceStatusError(
        err.message || "Ambulance status update failed."
      );
    } finally {
      setUpdatingAmbulanceId(null);
    }
  }

  async function findHospitals() {
    const emergency = emergencies.find(
      (item) => String(item.id) === selectedEmergency
    );

    if (!emergency) {
      setDispatchError("Select an emergency first.");
      return;
    }

    if (emergency.latitude == null || emergency.longitude == null) {
      setDispatchError("The selected emergency has no valid coordinates.");
      return;
    }

    setLoadingHospitals(true);
    setDispatchError("");
    setDispatchMessage("");
    setRecommendations([]);
    setSelectedHospital("");

    try {
      const response = await fetch(`${API}/recommend-hospitals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          latitude: emergency.latitude,
          longitude: emergency.longitude,
          limit: 5,
          description: emergency.description || "",
          category: emergency.category || "",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not recommend hospitals.");
      }

      const results = (data.recommendations || []).slice(0, 5);
      setRecommendations(results);

      if (results.length) {
        setSelectedHospital(String(results[0].id));
      } else {
        setDispatchError("No hospital candidates could be recommended.");
      }
    } catch (err) {
      setDispatchError(err.message || "Hospital recommendation failed.");
    } finally {
      setLoadingHospitals(false);
    }
  }

  async function createDispatch() {
    if (!selectedEmergency || !selectedAmbulance || !selectedHospital) {
      setDispatchError("Select an emergency, an ambulance, and a hospital.");
      return;
    }

    setSubmitting(true);
    setDispatchError("");
    setDispatchMessage("");

    try {
      const response = await fetch(`${API}/dispatches`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          emergency_id: Number(selectedEmergency),
          ambulance_id: Number(selectedAmbulance),
          hospital_id: selectedHospital,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Dispatch could not be created.");
      }

      setRoute(data.route || null);
      setDispatchMessage(`Dispatch #${data.dispatch_id} created successfully.`);
      setRecommendations([]);
      setSelectedHospital("");
      setSelectedAmbulance("");
      await refreshData();
    } catch (err) {
      setDispatchError(err.message || "Dispatch failed.");
    } finally {
      setSubmitting(false);
    }
  }

  function renderRecords() {
    const records = {
      Emergencies: emergencies,
      Ambulances: ambulances,
      Hospitals: filteredHospitals,
    }[page] || [];

    return (
      <>
        {page === "Emergencies" && <EmergencyForm onReported={refreshData} />}

        {page === "Hospitals" && (
          <input
            className="search-input"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search hospitals..."
          />
        )}

        {page === "Ambulances" && (
          <>
            <div className="stats-grid">
              <div className="stat-card">
                <span>Total Fleet</span>
                <h2>{ambulances.length}</h2>
              </div>
              <div className="stat-card">
                <span>🟢 Available</span>
                <h2>{availableAmbulances.length}</h2>
              </div>
              <div className="stat-card">
                <span>🔴 Busy / Assigned</span>
                <h2>{busyAmbulances.length}</h2>
              </div>
              <div className="stat-card">
                <span>🟡 Maintenance / Offline</span>
                <h2>{unavailableAmbulances.length}</h2>
              </div>
            </div>

            {ambulanceStatusError && (
              <p role="alert" style={{ color: "#b91c1c" }}>
                {ambulanceStatusError}
              </p>
            )}

            {ambulanceStatusMessage && (
              <p role="status" style={{ color: "#166534" }}>
                {ambulanceStatusMessage}
              </p>
            )}
          </>
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
            records.slice(0, 100).map((item, index) => {
              const status = (item.status || "").toLowerCase();

              return (
                <div className="incident" key={item.id ?? item.name ?? index}>
                  <div className="incident-title">
                    {page === "Hospitals"
                      ? "🏥 "
                      : page === "Ambulances"
                        ? "🚑 "
                        : "🚨 "}
                    {item.name || `#${item.id} · ${item.category || "Record"}`}
                  </div>

                  {page === "Ambulances" ? (
                    <>
                      <p className="incident-description">
                        Ambulance ID: {item.id}
                      </p>

                      <span
                        style={{
                          ...getStatusStyle(status),
                          display: "inline-block",
                          padding: "5px 10px",
                          borderRadius: "12px",
                          fontSize: "13px",
                          fontWeight: 600,
                          marginBottom: "12px",
                        }}
                      >
                        {getStatusLabel(status)}
                      </span>

                      <div style={{ maxWidth: "320px" }}>
                        <label>
                          Manage Status
                          <select
                            className="search-input"
                            value={status}
                            disabled={updatingAmbulanceId === item.id}
                            onChange={(event) =>
                              updateAmbulanceStatus(
                                item.id,
                                event.target.value
                              )
                            }
                          >
                            {AMBULANCE_STATUSES.map((option) => (
                              <option
                                key={option.value}
                                value={option.value}
                              >
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </label>
                        {updatingAmbulanceId === item.id && (
                          <span className="small-label">
                            Saving status...
                          </span>
                        )}
                      </div>

                      <span className="small-label">
                        Simulated location: {item.latitude ?? "—"},{" "}
                        {item.longitude ?? "—"}
                      </span>
                    </>
                  ) : (
                    <>
                      <p className="incident-description">
                        {item.description || item.status || item.category || "Hospital candidate"}
                      </p>
                      <span className="small-label">
                        Status: {item.status || "Unverified"} · Location:{" "}
                        {item.latitude ?? "—"}, {item.longitude ?? "—"}
                      </span>
                    </>
                  )}
                </div>
              );
            })
          )}
        </section>
      </>
    );
  }

  function renderDispatches() {
    const reportedEmergencies = activeEmergencies.filter(
      (item) => (item.status || "reported").toLowerCase() === "reported"
    );

    return (
      <>
        <section className="panel panel-body">
          <h3>Create Ambulance Dispatch</h3>
          <p>
            Assign an available simulated ambulance to an emergency and select
            a hospital candidate.
          </p>

          <div style={{ display: "grid", gap: "12px", maxWidth: "650px" }}>
            <label>
              Emergency
              <select
                className="search-input"
                value={selectedEmergency}
                onChange={(event) => {
                  setSelectedEmergency(event.target.value);
                  setRecommendations([]);
                  setSelectedHospital("");
                  setDispatchError("");
                  setDispatchMessage("");
                  setRoute(null);
                }}
              >
                <option value="">Select a reported emergency</option>
                {reportedEmergencies.map((item) => (
                  <option key={item.id} value={item.id}>
                    #{item.id} — {item.description || item.category}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Available Ambulance
              <select
                className="search-input"
                value={selectedAmbulance}
                onChange={(event) => setSelectedAmbulance(event.target.value)}
              >
                <option value="">Select an available ambulance</option>
                {availableAmbulances.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name || `Ambulance #${item.id}`} (ID: {item.id})
                  </option>
                ))}
              </select>
            </label>

            <button
              className="nav-item"
              onClick={findHospitals}
              disabled={loadingHospitals}
            >
              {loadingHospitals ? "Finding hospitals..." : "Find Recommended Hospitals"}
            </button>
          </div>

          {recommendations.length > 0 && (
            <div style={{ marginTop: "20px" }}>
              <h4>Hospital Recommendations</h4>
              <p className="small-label">
                Ranked using unverified name-based relevance hints, then
                calculated road distance. Medical suitability and current
                availability are not confirmed.
              </p>

              <div style={{ display: "grid", gap: "10px" }}>
                {recommendations.map((hospital, index) => (
                  <label
                    className="incident"
                    key={`${hospital.id}-${index}`}
                    style={{ cursor: "pointer" }}
                  >
                    <input
                      type="radio"
                      name="recommended-hospital"
                      value={String(hospital.id)}
                      checked={selectedHospital === String(hospital.id)}
                      onChange={(event) => setSelectedHospital(event.target.value)}
                    />{" "}
                    <strong>{hospital.name || "Unnamed candidate"}</strong>
                    <p className="incident-description">
                      Road distance: {hospital.road_distance_km} km
                    </p>
                    <span className="small-label">
                      {hospital.relevance_hint || "No clear name-based relevance hint"}
                    </span>
                  </label>
                ))}
              </div>

              <button
                className="nav-item active"
                onClick={createDispatch}
                disabled={submitting}
                style={{ marginTop: "14px" }}
              >
                {submitting ? "Creating dispatch..." : "Confirm Dispatch"}
              </button>
            </div>
          )}

          {dispatchError && (
            <p role="alert" style={{ color: "#b91c1c" }}>{dispatchError}</p>
          )}
          {dispatchMessage && (
            <p style={{ color: "#166534" }}>{dispatchMessage}</p>
          )}
        </section>

        {route && (
          <section className="panel panel-body">
            <h3>Calculated Ambulance Route</h3>
            <p>
              Road distance: <strong>{route.distance_km} km</strong>
            </p>
            <p className="small-label">
              Simulated shortest-distance route. Live traffic and travel time
              are not calculated.
            </p>
            <MapView route={route} />
          </section>
        )}

        <section className="panel panel-body">
          <h3>Dispatch History</h3>
          {!dispatches.length ? (
            <p>No dispatches recorded yet.</p>
          ) : (
            dispatches.map((item, index) => (
              <div className="incident" key={item.dispatch_id ?? item.id ?? index}>
                <div className="incident-title">
                  Dispatch #{item.dispatch_id ?? item.id ?? index + 1}
                </div>
                <p className="incident-description">
                  Emergency #{item.emergency_id} ·{" "}
                  {item.ambulance_name || `Ambulance #${item.ambulance_id}`}
                </p>
                <span className="small-label">
                  Status: {item.status || "Assigned"}
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
        <div className="topbar-actions">
          <span className="small-label">
            {online ? "🟢 Backend Online" : "🔴 Backend Offline"}
          </span>
          <span className="user-chip">
            {user.displayName || user.email || "Authenticated user"}
          </span>
          <button className="sign-out-button" onClick={logOut}>
            Sign out
          </button>
        </div>
      </header>

      <div className="app-layout">
        <aside className="sidebar">
          <h3>Navigation</h3>
          {NAV.map((item) => (
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
                {[
                  ["Active Emergencies", activeEmergencies.length],
                  ["Ambulances Available", availableAmbulances.length],
                  ["Ambulances Busy", busyAmbulances.length],
                  ["Hospital Candidates", hospitals.length],
                  ["Dispatches Recorded", dispatches.length],
                ].map(([label, value]) => (
                  <div className="stat-card" key={label}>
                    <span>{label}</span>
                    <h2>{value}</h2>
                  </div>
                ))}
              </div>

              <section className="panel panel-body">
                <h3>Ambulance Fleet Status</h3>
                {!ambulances.length ? (
                  <p>No ambulances available.</p>
                ) : (
                  <div style={{ display: "grid", gap: "10px" }}>
                    {ambulances.map((item) => (
                      <div
                        key={item.id}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          gap: "12px",
                          flexWrap: "wrap",
                        }}
                      >
                        <span>
                          🚑 {item.name || `Ambulance #${item.id}`}
                        </span>
                        <span
                          style={{
                            ...getStatusStyle(item.status),
                            padding: "5px 10px",
                            borderRadius: "12px",
                            fontSize: "13px",
                            fontWeight: 600,
                          }}
                        >
                          {getStatusLabel(item.status)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                <button
                  className="nav-item"
                  onClick={() => setPage("Ambulances")}
                  style={{ marginTop: "16px" }}
                >
                  Manage Ambulances
                </button>
              </section>

              <section className="panel panel-body">
                <h3>Nagpur Emergency Map</h3>
                <MapView route={route} />
              </section>

              <section className="panel panel-body">
                <h3>Recent Emergencies</h3>
                {!emergencies.length ? (
                  <p>No emergencies reported yet.</p>
                ) : (
                  emergencies.slice(0, 5).map((item, index) => (
                    <div className="incident" key={item.id ?? index}>
                      <div className="incident-title">
                        🚨 {item.category || `Emergency #${item.id}`}
                      </div>
                      <p className="incident-description">{item.description}</p>
                      <span className="small-label">
                        Status: {item.status || "Reported"}
                      </span>
                    </div>
                  ))
                )}
              </section>
            </>
          ) : page === "Dispatches" ? (
            renderDispatches()
          ) : (
            renderRecords()
          )}

          <footer className="footer">
            Academic proof of concept. Emergency data, ambulance operations,
            hospital availability, and dispatches are simulated or unverified
            where indicated.
          </footer>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(undefined);

  useEffect(() => onAuthChange(setUser), []);

  if (user === undefined) {
    return <div className="auth-loading">Loading your secure workspace...</div>;
  }

  return user ? <DashboardApp user={user} /> : <LoginPage />;
}
