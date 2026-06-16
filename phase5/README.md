# TransRoute Planner – Phase 5: Graphical Interface

## System Requirements
- Python 3.10+
- Docker Desktop (running with the `integrated_db` PostgreSQL container)
- Internet connection (for map tiles from OpenStreetMap)

---

## Quick Start

### Step 1 – Ensure Docker is running
Make sure your Docker containers are up:
```bash
cd "<project root>"
docker-compose up -d
```
The PostgreSQL DB should be reachable at **localhost:5433** with database `integrated_db`.

### Step 2 – Install Python dependencies
Open a terminal in the `phase5` folder and run:
```bash
pip install -r requirements.txt
```

### Step 3 – Launch the application
```bash
python main.py
```

---

## Screens

| Screen | Description |
|--------|-------------|
| 🏠 Dashboard | Live statistics cards, recent trips, routes-by-region chart |
| 🗺️ Routes | Full CRUD + interactive map of route stops |
| 🚌 Trips | Full CRUD + occupancy color coding + date filter |
| 🚗 Vehicles | Full CRUD + trip history detail |
| 🧑‍✈️ Drivers | Full CRUD + upcoming schedule |
| 👤 Passengers & Registrations | CRUD for both tables; status change fires DB triggers |
| 📍 Stops | Full CRUD + live map pin for each stop |
| 📊 Queries & Procedures | Phase-2 queries + Phase-4 procedures/functions |

---

## Queries & Procedures Screen

### Phase 2 Queries
- **Query 1A** – Routes dashboard: JOIN region + GROUP BY stop count
- **Query 6** – Avg duration & distance per region (AVG + HAVING)

### Phase 4 Stored Procedures / Functions
| Name | Type | Description |
|------|------|-------------|
| `get_route_dashboard()` | Function (Ref Cursor) | Returns route dashboard data |
| `calculate_trip_occupancy(trip_id)` | Table Function | Occupancy % + status per trip |
| `schedule_new_trip(…)` | Procedure | Validates & inserts a new trip |
| `auto_assign_drivers_to_future_trips()` | Procedure | Round-Robin driver assignment |

---

## Database Connection
Edit `db_connection.py` if your settings differ:
```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     5433,
    "database": "integrated_db",
    "user":     "efrat",
    "password": "efrat",
}
```

---

## Project Structure
```
phase5/
├── main.py                    # App entry point + sidebar navigation
├── db_connection.py           # DB helpers (fetch, execute, call procedures)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── screens/
    ├── __init__.py
    ├── base_screen.py         # Shared base class + UI helpers
    ├── dashboard_screen.py    # Home dashboard
    ├── routes_screen.py       # Routes CRUD + map
    ├── trips_screen.py        # Trips CRUD
    ├── vehicles_screen.py     # Vehicles CRUD
    ├── drivers_screen.py      # Drivers CRUD
    ├── passengers_screen.py   # Passengers + Registrations CRUD
    ├── stops_screen.py        # Stops CRUD + map
    └── queries_screen.py      # Phase-2 queries + Phase-4 procedures
```
