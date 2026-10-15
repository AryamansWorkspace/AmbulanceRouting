
import { useState } from "react";
import MapView from "./MapView";

const initialStats = [
  {
    label: "Active Emergencies",
    value: "0",
    icon: "🚨",
    note: "No reports yet",
  },
  {
    label: "Available Ambulances",
    value: "3",
    icon: "🚑",
    note: "Simulated fleet",
  },
  {
    label: "Hospitals Tracked",
    value: "5",
    icon: "🏥",
    note: "Sample locations",
  },
  {
    label: "Routes Calculated",
    value: "0",
    icon: "🗺️",
    note: "Awaiting requests",
  },
];

function App() {
  const [activePage, setActivePage] = useState("Dashboard");

  const navItems = [
    { label: "Dashboard", icon: "▦" },
    { label: "Emergencies", icon: "🚨" },
    { label: "Ambulances", icon: "🚑" },
    { label: "Hospitals", icon: "🏥" },
  ];

  return (
    <div className="app">
      <style>{`
        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          font-family: Arial, Helvetica, sans-serif;
          background: #f4f7fb;
          color: #172033;
        }

        button {
          font: inherit;
          cursor: pointer;
        }

        .app {
          min-height: 100vh;
        }

        .topbar {
          height: 72px;
          background: #fff;
          border-bottom: 1px solid #e5eaf1;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 32px;
          gap: 16px;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 12px;
          min-width: 0;
        }

        .brand-icon {
          width: 42px;
          height: 42px;
          border-radius: 12px;
          display: grid;
          place-items: center;
          background: #e8f1ff;
          font-size: 23px;
        }

        .brand-title {
          font-weight: 700;
          font-size: 17px;
        }

        .brand-subtitle {
          color: #7b8799;
          font-size: 12px;
          margin-top: 4px;
        }

        .system-status {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          color: #526174;
          white-space: nowrap;
        }

        .status-dot {
          width: 9px;
          height: 9px;
          border-radius: 50%;
          background: #22a06b;
        }

        .layout {
          display: flex;
          min-height: calc(100vh - 72px);
        }

        .sidebar {
          width: 220px;
          background: #fff;
          border-right: 1px solid #e5eaf1;
          padding: 25px 14px;
          flex-shrink: 0;
        }

        .nav-heading {
          padding: 0 12px;
          margin-bottom: 12px;
          color: #929db0;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 1px;
        }

        .nav-item {
          width: 100%;
          border: 0;
          border-radius: 9px;
          background: transparent;
          padding: 12px;
          display: flex;
          align-items: center;
          gap: 12px;
          color: #536176;
          text-align: left;
          margin-bottom: 5px;
          font-size: 14px;
        }

        .nav-item.active {
          background: #eaf2ff;
          color: #1d5fc4;
          font-weight: 700;
        }

        .nav-icon {
          width: 22px;
          text-align: center;
          font-size: 17px;
        }

        .sidebar-note {
          margin: 35px 6px 0;
          padding: 14px;
          border-radius: 10px;
          background: #f5f8fc;
          color: #68768a;
          font-size: 12px;
          line-height: 1.6;
        }

        .sidebar-note strong {
          display: block;
          color: #26354a;
          margin-bottom: 5px;
        }

        .main {
          flex: 1;
          min-width: 0;
          padding: 30px 32px;
        }

        .page-heading {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 16px;
          margin-bottom: 24px;
        }

        h1 {
          margin: 0;
          font-size: 26px;
          letter-spacing: -0.5px;
        }

        .page-description {
          margin: 8px 0 0;
          color: #758196;
          font-size: 14px;
          line-height: 1.5;
        }

        .demo-badge {
          background: #fff4dc;
          color: #946200;
          border: 1px solid #f4dfae;
          border-radius: 20px;
          padding: 8px 12px;
          font-size: 12px;
          white-space: nowrap;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }

        .stat-card,
        .panel {
          background: #fff;
          border: 1px solid #e5eaf1;
          border-radius: 13px;
        }

        .stat-card {
          padding: 20px;
        }

        .stat-top {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }

        .stat-icon {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: grid;
          place-items: center;
          background: #f0f5fc;
          font-size: 20px;
        }

        .stat-value {
          font-size: 28px;
          font-weight: 700;
          margin-top: 16px;
        }

        .stat-note {
          font-size: 11px;
          color: #929db0;
          margin-top: 10px;
        }

        .content-grid {
          display: grid;
          grid-template-columns: minmax(0, 1.7fr) minmax(250px, 1fr);
          gap: 20px;
        }

        .panel {
          overflow: hidden;
          min-width: 0;
        }

        .panel-header {
          padding: 19px 20px;
          border-bottom: 1px solid #edf0f5;
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
        }

        .panel-title {
          font-size: 15px;
          font-weight: 700;
        }

        .panel-subtitle {
          font-size: 12px;
          color: #8792a4;
          margin-top: 5px;
        }

        .small-label {
          color: #778499;
          font-size: 12px;
        }

        .map-container {
          height: 360px;
          width: 100%;
          background: #edf3f8;
        }

        .map-container .leaflet-container {
          height: 100%;
          width: 100%;
          z-index: 1;
        }

        .panel-body {
          padding: 20px;
        }

        .empty-state {
          text-align: center;
          padding: 25px 10px;
        }

        .empty-icon {
          font-size: 28px;
        }

        .empty-state h3 {
          margin: 12px 0 7px;
          font-size: 14px;
        }

        .empty-state p {
          color: #8490a2;
          font-size: 12px;
          line-height: 1.6;
          margin: 0 auto;
          max-width: 230px;
        }

        .primary-button {
          margin-top: 18px;
          border: 0;
          border-radius: 8px;
          background: #2165cc;
          color: white;
          padding: 10px 14px;
          font-size: 12px;
          font-weight: 700;
        }

        .primary-button:hover {
          background: #194fa4;
        }

        .footer-note {
          color: #8a95a6;
          font-size: 11px;
          margin-top: 24px;
          line-height: 1.6;
        }

        @media (max-width: 1100px) {
          .stats-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .content-grid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 700px) {
          .topbar {
            padding: 0 16px;
            height: 64px;
          }

          .brand-title {
            font-size: 14px;
          }

          .brand-subtitle {
            font-size: 11px;
          }

          .system-status {
            font-size: 0;
          }

          .sidebar {
            width: 64px;
            padding: 20px 8px;
          }

          .nav-heading,
          .nav-text,
          .sidebar-note {
            display: none;
          }

          .nav-item {
            justify-content: center;
            padding: 12px 5px;
          }

          .nav-icon {
            font-size: 18px;
          }

          .main {
            padding: 22px 14px;
          }

          .page-heading {
            flex-direction: column;
          }

          h1 {
            font-size: 23px;
          }

          .stats-grid {
            gap: 10px;
          }

          .stat-card {
            padding: 14px;
          }

          .stat-value {
            font-size: 24px;
          }

          .map-container {
            height: 320px;
          }
        }
      `}</style>

      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">🚑</div>
          <div>
            <div className="brand-title">Emergency Response Twin</div>
            <div className="brand-subtitle">
              Ambulance Routing & Management
            </div>
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot" />
          Backend online
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <div className="nav-heading">WORKSPACE</div>

          {navItems.map((item) => (
            <button
              key={item.label}
              className={`nav-item ${
                activePage === item.label ? "active" : ""
              }`}
              onClick={() => setActivePage(item.label)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-text">{item.label}</span>
            </button>
          ))}

          <div className="sidebar-note">
            <strong>Proof of Concept</strong>
            This dashboard uses simulated emergency and fleet data for
            demonstration.
          </div>
        </aside>

        <main className="main">
          <div className="page-heading">
            <div>
              <h1>{activePage}</h1>
              <p className="page-description">
                Monitor emergency response activity across the Nagpur
                demonstration area.
              </p>
            </div>

            <span className="demo-badge">● Simulation Mode</span>
          </div>

          <section className="stats-grid">
            {initialStats.map((stat) => (
              <div className="stat-card" key={stat.label}>
                <div className="stat-top">
                  <span className="small-label">{stat.label}</span>
                  <span className="stat-icon">{stat.icon}</span>
                </div>

                <div className="stat-value">{stat.value}</div>
                <div className="stat-note">{stat.note}</div>
              </div>
            ))}
          </section>

          <section className="content-grid">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <div className="panel-title">
                    Emergency & Fleet Map
                  </div>
                  <div className="panel-subtitle">
                    Geographic view of the demonstration area
                  </div>
                </div>

                <span className="small-label">Nagpur, India</span>
              </div>

              <div className="map-container">
                <MapView />
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <div className="panel-title">Recent Emergencies</div>
                  <div className="panel-subtitle">
                    Latest reported incidents
                  </div>
                </div>

                <span className="small-label">0 reports</span>
              </div>

              <div className="panel-body">
                <div className="empty-state">
                  <div className="empty-icon">📋</div>
                  <h3>No emergencies reported</h3>
                  <p>
                    Reported incidents will appear here when the emergency
                    reporting form is implemented.
                  </p>

                  <button
                    className="primary-button"
                    onClick={() => setActivePage("Emergencies")}
                  >
                    View Emergencies
                  </button>
                </div>
              </div>
            </div>
          </section>

          <p className="footer-note">
            Academic proof of concept · Sample figures are placeholders, not
            live emergency service data.
          </p>
        </main>
      </div>
    </div>
  );
}

export default App;
