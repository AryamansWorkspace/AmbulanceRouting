import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent / "data" / "ambulance.db"


def get_connection():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection



def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS emergencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                category TEXT NOT NULL,
                confidence REAL,
                status TEXT NOT NULL DEFAULT 'reported',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ambulances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'available'
            );

            CREATE TABLE IF NOT EXISTS dispatches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emergency_id INTEGER NOT NULL,
                ambulance_id INTEGER,
                hospital_id TEXT,
                status TEXT NOT NULL DEFAULT 'assigned',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emergency_id) REFERENCES emergencies(id),
                FOREIGN KEY (ambulance_id) REFERENCES ambulances(id)
            );
        """)

        ambulances = [
            ("Simulated Ambulance 1", 21.1458, 79.0882),
            ("Simulated Ambulance 2", 21.1702, 79.0470),
            ("Simulated Ambulance 3", 21.1200, 79.1300),
            ("Simulated Ambulance 4", 21.1550, 79.0800),
            ("Simulated Ambulance 5", 21.1600, 79.1000),
            ("Simulated Ambulance 6", 21.1350, 79.0700),
            ("Simulated Ambulance 7", 21.1800, 79.0900),
            ("Simulated Ambulance 8", 21.1100, 79.1100),
            ("Simulated Ambulance 9", 21.1500, 79.1200),
            ("Simulated Ambulance 10", 21.1250, 79.0600),
        ]

        conn.executemany(
            """
            INSERT OR IGNORE INTO ambulances (name, latitude, longitude)
            VALUES (?, ?, ?)
            """,
            ambulances,
        )



if __name__ == "__main__":
    init_db()
    print(f"Database initialized: {DB_FILE}")
