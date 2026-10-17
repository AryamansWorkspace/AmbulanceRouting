import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  Polyline,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

const API = "http://127.0.0.1:8000";

const TRAFFIC_COLORS = {
  free: "#16a34a",
  moderate: "#eab308",
  heavy: "#ea580c",
  blocked: "#dc2626",
};

function MapView({
  route = null,
  trafficScenario = "baseline",
  onTrafficScenarioChange = () => {},
}) {
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [trafficSegments, setTrafficSegments] = useState([]);

  useEffect(() => {
    fetch(`${API}/hospitals`)
      .then((response) => {
        if (!response.ok) throw new Error("Hospital data unavailable.");
        return response.json();
      })
      .then(setHospitals)
      .catch(() =>
        setError("Unable to load hospitals. Check the backend.")
      )
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const scenario =
      trafficScenario === "baseline" ? "normal" : trafficScenario;

    fetch(
      `${API}/traffic-simulation?scenario=${scenario}`
    )
      .then((response) => {
        if (!response.ok) throw new Error("Traffic overlay unavailable.");
        return response.json();
      })
      .then((data) => setTrafficSegments(data.segments || []))
      .catch(() => setTrafficSegments([]));
  }, [trafficScenario]);

  const statusColor = (status) =>
    TRAFFIC_COLORS[status] || "#2563eb";

  return (
    <div style={{ width: "100%" }}>
      <div
        style={{
          display: "flex",
          gap: "12px",
          alignItems: "center",
          flexWrap: "wrap",
          marginBottom: "12px",
        }}
      >
        <label>
          Traffic scenario{" "}
          <select
            className="search-input"
            style={{ width: "220px", marginTop: "8px" }}
            value={trafficScenario}
            onChange={(event) =>
              onTrafficScenarioChange(event.target.value)
            }
          >
            <option value="baseline">Baseline · Shortest distance</option>
            <option value="normal">Normal traffic</option>
            <option value="congested">Heavy congestion</option>
            <option value="blockage">Road blockage</option>
          </select>
        </label>
        <span className="small-label">
          Simulated conditions · Not live traffic
        </span>
      </div>

      <div
        style={{
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
          marginBottom: "10px",
          fontSize: "12px",
        }}
      >
        {[
          ["#16a34a", "Free"],
          ["#eab308", "Moderate"],
          ["#ea580c", "Heavy"],
          ["#dc2626", "Blocked"],
        ].map(([color, label]) => (
          <span key={label}>
            <span style={{ color, fontWeight: 800 }}>━━</span> {label}
          </span>
        ))}
      </div>

      {loading && <p>Loading hospital locations...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && (
        <p>Hospital locations loaded: {hospitals.length}</p>
      )}

      {route?.estimated_time_min != null && (
        <p>
          <strong>Estimated travel time:</strong>{" "}
          {route.estimated_time_min} minutes
          {" · "}
          <strong>Distance:</strong> {route.distance_km} km
        </p>
      )}

      <MapContainer
        center={[21.1458, 79.0882]}
        zoom={12}
        scrollWheelZoom={true}
        style={{ height: "420px", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {trafficSegments.map((segment) => (
          <Polyline
            key={segment.id}
            positions={segment.coordinates}
            pathOptions={{
              color: statusColor(segment.status),
              weight: segment.status === "blocked" ? 5 : 3,
              opacity: 0.7,
            }}
          >
            <Popup>
              <strong>Simulated road condition</strong>
              <br />
              Status: {segment.status}
              <br />
              Estimated speed: {segment.speed_kmh} km/h
            </Popup>
          </Polyline>
        ))}

        {route?.route_segments?.length > 0
          ? route.route_segments.map((segment, index) => (
              <Polyline
                key={`route-${index}`}
                positions={segment.coordinates}
                pathOptions={{
                  color: statusColor(segment.status),
                  weight: 7,
                  opacity: 1,
                }}
              >
                <Popup>
                  Ambulance route · {segment.status}
                </Popup>
              </Polyline>
            ))
          : route?.coordinates?.length > 1 && (
              <Polyline
                positions={route.coordinates}
                pathOptions={{
                  color: "#2563eb",
                  weight: 6,
                  opacity: 0.95,
                }}
              >
                <Popup>
                  <strong>Baseline ambulance route</strong>
                  <br />
                  Road distance: {route.distance_km} km
                  <br />
                  Travel time is not estimated for the baseline.
                </Popup>
              </Polyline>
            )}

        {hospitals.map((hospital) => (
          <CircleMarker
            key={hospital.id}
            center={[hospital.latitude, hospital.longitude]}
            radius={6}
            pathOptions={{
              color: "#155e75",
              fillColor: "#06b6d4",
              fillOpacity: 0.85,
            }}
          >
            <Popup>
              <strong>{hospital.name}</strong>
              <br />
              Source: {hospital.source}
              <br />
              Status: Unverified
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}

export default MapView;