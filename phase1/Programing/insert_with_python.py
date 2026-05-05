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
# Seed base reference tables (INSERT OR IGNORE)
# -------------------------------------------------------

# REGION
cur.executemany("""
    INSERT INTO region (region_id, regio_name, terrain_type, description)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT DO NOTHING
""", [
    (1, "North",     "Mountain",  "Northern mountainous region"),
    (2, "South",     "Desert",    "Southern desert region"),
    (3, "East",      "Forest",    "Eastern forest region"),
    (4, "West",      "Coastal",   "Western coastal region"),
    (5, "Central",   "Plains",    "Central plains region"),
    (6, "Northeast", "Highland",  "Northeastern highland region"),
    (7, "Northwest", "Valley",    "Northwestern valley region"),
    (8, "Southeast", "Wetland",   "Southeastern wetland region"),
    (9, "Southwest", "Savanna",   "Southwestern savanna region"),
    (10,"Midland",   "Urban",     "Midland urban region"),
])
conn.commit()

# VEHICLE
cur.executemany("""
    INSERT INTO vehicle (plate_number, vehicle_type, capacity)
    VALUES (%s, %s, %s)
    ON CONFLICT DO NOTHING
""", [
    ("IL-100-AA", "Bus",        52), ("IL-101-BB", "Bus",        52),
    ("IL-102-CC", "Minibus",    20), ("IL-103-DD", "Minibus",    20),
    ("IL-104-EE", "Van",        12), ("IL-105-FF", "Van",        12),
    ("IL-106-GG", "Coach",      60), ("IL-107-HH", "Coach",      60),
    ("IL-108-II", "Bus",        52), ("IL-109-JJ", "Minibus",    25),
    ("IL-110-KK", "Van",        14), ("IL-111-LL", "Coach",      55),
    ("IL-112-MM", "Bus",        48), ("IL-113-NN", "Minibus",    22),
    ("IL-114-OO", "Van",        10), ("IL-115-PP", "Coach",      62),
    ("IL-116-QQ", "Bus",        50), ("IL-117-RR", "Minibus",    18),
    ("IL-118-SS", "Van",        13), ("IL-119-TT", "Coach",      58),
])
conn.commit()

# SITE
cur.executemany("""
    INSERT INTO site (site_name, site_type, address)
    VALUES (%s, %s, %s)
    ON CONFLICT DO NOTHING
""", [
    ("Tel Aviv Central",  "Station",    "Arlozorov 1, Tel Aviv"),
    ("Jerusalem Central", "Station",    "Jaffa Rd 224, Jerusalem"),
    ("Haifa Central",     "Station",    "HaNamal St 1, Haifa"),
    ("Beer Sheva Central","Station",    "Egged St 1, Beer Sheva"),
    ("Eilat Station",     "Station",    "Hatmarim Blvd 1, Eilat"),
    ("Tiberias Station",  "Station",    "HaYarden St 5, Tiberias"),
    ("Nazareth Station",  "Station",    "Paulus VI St 1, Nazareth"),
    ("Ashdod Station",    "Station",    "Menachem Begin Blvd 10, Ashdod"),
    ("Netanya Station",   "Station",    "HaAtzmaut Sq, Netanya"),
    ("Rishon LeZion Stn", "Station",    "Herzl St 1, Rishon LeZion"),
])
conn.commit()

# STOP
cur.executemany("""
    INSERT INTO stop (stop_id, stop_name, address, latitude, longitude, site_name)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING
""", [
    (1,  "Tel Aviv Central",   "Arlozorov 1, Tel Aviv",          32.0853,  34.7818, "Tel Aviv Central"),
    (2,  "Jerusalem Central",  "Jaffa Rd 224, Jerusalem",        31.7857,  35.2007, "Jerusalem Central"),
    (3,  "Haifa Central",      "HaNamal St 1, Haifa",            32.8191,  34.9989, "Haifa Central"),
    (4,  "Beer Sheva Central", "Egged St 1, Beer Sheva",         31.2518,  34.7915, "Beer Sheva Central"),
    (5,  "Eilat Station",      "Hatmarim Blvd 1, Eilat",         29.5577,  34.9519, "Eilat Station"),
    (6,  "Tiberias Station",   "HaYarden St 5, Tiberias",        32.7940,  35.5300, "Tiberias Station"),
    (7,  "Nazareth Station",   "Paulus VI St 1, Nazareth",       32.6996,  35.3035, "Nazareth Station"),
    (8,  "Ashdod Station",     "Menachem Begin Blvd 10, Ashdod", 31.8040,  34.6550, "Ashdod Station"),
    (9,  "Netanya Station",    "HaAtzmaut Sq, Netanya",          32.3215,  34.8532, "Netanya Station"),
    (10, "Rishon LeZion Stn",  "Herzl St 1, Rishon LeZion",      31.9642,  34.8007, "Rishon LeZion Stn"),
])
conn.commit()

# ROUTE
cur.executemany("""
    INSERT INTO route (route_id, route_name, start_location, end_location,
                       estimated_duration_minutes, total_distance_km, created_date, region_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING
""", [
    (1,  "TLV-JER Express",   "Tel Aviv",    "Jerusalem",   90,  60.0,  "2024-01-01", 5),
    (2,  "TLV-HFA Line",      "Tel Aviv",    "Haifa",       60,  90.0,  "2024-01-01", 1),
    (3,  "JER-BSV Route",     "Jerusalem",   "Beer Sheva",  75,  85.0,  "2024-01-01", 2),
    (4,  "HFA-TBR Line",      "Haifa",       "Tiberias",    45,  50.0,  "2024-01-01", 3),
    (5,  "BSV-ELT Desert",    "Beer Sheva",  "Eilat",       180, 240.0, "2024-01-01", 2),
    (6,  "TLV-ASH Shuttle",   "Tel Aviv",    "Ashdod",      30,  35.0,  "2024-01-01", 4),
    (7,  "TLV-NET Coastal",   "Tel Aviv",    "Netanya",     40,  45.0,  "2024-01-01", 4),
    (8,  "TLV-RSL City",      "Tel Aviv",    "Rishon",      20,  15.0,  "2024-01-01", 5),
    (9,  "NZR-TBR Highland",  "Nazareth",    "Tiberias",    35,  40.0,  "2024-01-01", 6),
    (10, "HFA-NZR Valley",    "Haifa",       "Nazareth",    40,  30.0,  "2024-01-01", 7),
])
conn.commit()
print("Seeded base tables: region, vehicle, site, stop, route")

# -------------------------------------------------------
# Load reference data
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
for trip_id in range(20002, 20101):
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
seen_route_stop = set()
route_stop_rows = []
while len(seen_route_stop) < min(100, len(route_ids) * len(stop_ids)):
    route_id   = random.choice(route_ids)
    stop_id    = random.choice(stop_ids)
    key        = (route_id, stop_id)
    if key in seen_route_stop:
        continue
    seen_route_stop.add(key)
    stop_order = len(seen_route_stop)   # unique order per route kept simple
    arrival    = random.choice(departure_times)
    route_stop_rows.append((stop_order, arrival, route_id, stop_id))

cur.executemany("""
    INSERT INTO route_stop (stop_order, estimated_arrival_time, route_id, stop_id)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT DO NOTHING
""", route_stop_rows)
conn.commit()
print("Inserted ROUTE_STOP rows")

# -------------------------------------------------------
# 3. REGION_VEHICLE -- ~500 unique (region_id, plate_number) pairs
#    Depends on: REGION (region_id), VEHICLE (plate_number)
# -------------------------------------------------------
max_region_vehicle = len(region_ids) * len(plate_numbers)  # 10*20=200
region_vehicle_rows = set()
while len(region_vehicle_rows) < min(200, max_region_vehicle):
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
