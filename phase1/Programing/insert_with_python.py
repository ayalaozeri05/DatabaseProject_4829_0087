import os
import random
from datetime import date, timedelta

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------
# Connect to PostgreSQL
# -------------------------------------------------------
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=os.getenv("DB_PORT", "5433"),
    dbname=os.getenv("DB_NAME_SECRET"),
    user=os.getenv("DB_USER_SECRET"),
    password=os.getenv("DB_PASSWORD_SECRET"),
)
cur = conn.cursor()

# -------------------------------------------------------
# Load existing reference data from pgAdmin-populated tables
# -------------------------------------------------------
cur.execute("SELECT plate_number FROM vehicle")
plate_numbers = [row[0] for row in cur.fetchall()]

cur.execute("SELECT route_id FROM route")
route_ids = [row[0] for row in cur.fetchall()]

cur.execute("SELECT stop_id FROM stop")
stop_ids = [row[0] for row in cur.fetchall()]

cur.execute("SELECT region_id FROM region")
region_ids = [row[0] for row in cur.fetchall()]

print("Loaded: %d vehicles, %d routes, %d stops, %d regions" % (
    len(plate_numbers), len(route_ids), len(stop_ids), len(region_ids)))

# -------------------------------------------------------
# 1. TRIP -- 20,000 rows
#    Depends on: VEHICLE (plate_number), ROUTE (route_id)
# -------------------------------------------------------
departure_times = [
    "06:00", "06:30", "07:00", "07:30", "08:00", "08:30",
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "13:00", "13:30", "14:00", "14:30",
    "15:00", "15:30", "16:00", "16:30", "17:00", "17:30",
    "18:00", "18:30", "19:00", "19:30", "20:00", "20:30",
    "21:00", "21:30", "22:00"
]

start_date = date(2025, 1, 1)
end_date   = date(2026, 12, 31)
days_range = (end_date - start_date).days

trip_rows = []
for trip_id in range(1, 20001):
    trip_rows.append((
        trip_id,
        start_date + timedelta(days=random.randint(0, days_range)),
        random.choice(departure_times),
        random.randint(0, 52),
        random.choice(route_ids),
        random.choice(plate_numbers),
    ))

cur.executemany("""
    INSERT INTO trip (trip_id, trip_date, departure_time, available_seats, route_id, plate_number)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING
""", trip_rows)
conn.commit()
print("Inserted 20,000 rows into TRIP")

# -------------------------------------------------------
# 2. ROUTE_STOP -- ~20,000 unique (route_id, stop_id) pairs
#    Depends on: ROUTE (route_id), STOP (stop_id)
#    Constraints: PK (route_id, stop_id), UNIQUE (route_id, stop_order)
# -------------------------------------------------------
route_stop_rows = set()
while len(route_stop_rows) < 20000:
    route_id   = random.choice(route_ids)
    stop_id    = random.choice(stop_ids)
    stop_order = random.randint(1, 20)
    arrival    = random.choice(departure_times)
    route_stop_rows.add((stop_order, arrival, route_id, stop_id))

cur.executemany("""
    INSERT INTO route_stop (stop_order, estimated_arrival_time, route_id, stop_id)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT DO NOTHING
""", list(route_stop_rows))
conn.commit()
print("Inserted ROUTE_STOP rows")

# -------------------------------------------------------
# 3. REGION_VEHICLE -- ~500 unique (region_id, plate_number) pairs
#    Depends on: REGION (region_id), VEHICLE (plate_number)
# -------------------------------------------------------
region_vehicle_rows = set()
while len(region_vehicle_rows) < 500:
    region_vehicle_rows.add((
        random.choice(region_ids),
        random.choice(plate_numbers),
    ))

cur.executemany("""
    INSERT INTO region_vehicle (region_id, plate_number)
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING
""", list(region_vehicle_rows))
conn.commit()
print("Inserted REGION_VEHICLE rows")

# -------------------------------------------------------
cur.close()
conn.close()
print("Done.")
