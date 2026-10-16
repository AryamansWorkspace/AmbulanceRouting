
import { useState } from "react";

const API = "http://127.0.0.1:8000";

export default function EmergencyForm({ onReported }) {
  const [description, setDescription] = useState("");
  const [query, setQuery] = useState("");
  const [locations, setLocations] = useState([]);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function searchLocation(e) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    setSelected(null);
    setLocations([]);

    try {
      const res = await fetch(
        `${API}/geocode?q=${encodeURIComponent(query.trim())}`
      );
      const data = await res.json();
      if (!res.ok) throw Error(data.detail || "Location search failed.");
      setLocations(data.results || []);
      if (!data.results?.length) setMessage("No matching locations found.");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function submitEmergency(e) {
    e.preventDefault();
    if (!selected) return setMessage("Search for and select a location.");

    setBusy(true);
    setMessage("");

    try {
      const res = await fetch(`${API}/emergencies`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: description.trim(),
          latitude: selected.latitude,
          longitude: selected.longitude,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw Error(data.detail || "Submission failed.");

      setDescription("");
      setQuery("");
      setLocations([]);
      setSelected(null);
      setMessage(`Emergency reported successfully. ID: ${data.id}`);
      onReported();
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel panel-body">
      <h3>Report New Emergency</h3>
      <form onSubmit={submitEmergency}>
        <label htmlFor="description">Incident Description</label>
        <textarea
          id="description"
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="Describe the emergency..."
          minLength={3}
          maxLength={500}
          required
          rows={3}
          style={{ display: "block", width: "100%", padding: 10,
            margin: "8px 0 14px", boxSizing: "border-box" }}
        />

        <label htmlFor="location">Emergency Location</label>
        <div style={{ display: "flex", gap: 8, margin: "8px 0 14px" }}>
          <input
            id="location"
            value={query}
            onChange={e => {
              setQuery(e.target.value);
              setLocations([]);
              setSelected(null);
            }}
            placeholder="e.g. Sitabuldi, Nagpur"
            minLength={3}
            required
            style={{ flex: 1, minWidth: 0, padding: 10 }}
          />
          <button type="button" disabled={busy} onClick={searchLocation}>
            {busy ? "Please wait..." : "Search"}
          </button>
        </div>

        {locations.map((loc, i) => (
          <label key={i} style={{ display: "flex", gap: 8, padding: 8 }}>
            <input
              type="radio"
              name="location"
              checked={selected === loc}
              onChange={() => setSelected(loc)}
            />
            <span>{loc.name}</span>
          </label>
        ))}

        <button type="submit" disabled={busy || !selected}>
          Report Emergency
        </button>
      </form>
      {message && <p role="status">{message}</p>}
    </div>
  );
}
