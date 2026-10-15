
import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

function MapView() {
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/hospitals")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Could not load hospital data.");
        }
        return response.json();
      })
      .then((data) => setHospitals(data))
      .catch(() => setError("Unable to load hospitals. Check that the backend is running."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ width: "100%" }}>
      {loading && <p>Loading hospital locations...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && (
        <p>Hospital locations loaded: {hospitals.length}</p>
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
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}

export default MapView;
