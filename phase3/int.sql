-- ========================================================
-- int.sql - אינטגרציה של שלב ג'
-- הרצה על: integrated_db
-- מסד נתונים מקור: other_db_temp
-- הנחת יסוד: integrated_db כבר מכיל את הנתונים של המערכת המקורית.
-- מטרה: הוספת המבנה והנתונים של המערכת השנייה ללא מחיקת הנתונים הקיימים.
-- ========================================================

BEGIN;

-- ========================================================
-- 0) הפעלת הרחבת dblink
-- ========================================================
CREATE EXTENSION IF NOT EXISTS dblink;

-- ========================================================
-- 1) הוספת הטבלאות החסרות מהמערכת השנייה
-- ========================================================
CREATE TABLE IF NOT EXISTS public.driver (
    driver_id INTEGER PRIMARY KEY,
    driver_fullname VARCHAR,
    phone VARCHAR,
    license_number VARCHAR
);

CREATE TABLE IF NOT EXISTS public.passenger (
    pass_id INTEGER PRIMARY KEY,
    pass_fullname VARCHAR,
    phone VARCHAR
);

CREATE TABLE IF NOT EXISTS public.registration (
    reg_id INTEGER PRIMARY KEY,
    status VARCHAR,
    pass_id INTEGER,
    trip_id INTEGER,
    boarding_stop_id INTEGER,
    dropoff_stop_id INTEGER
);

CREATE TABLE IF NOT EXISTS public.includes (
    route_id INTEGER,
    stop_id INTEGER
);

-- ========================================================
-- 2) הוספת עמודות חסרות והרחבת שדות טקסט קצרים
-- ========================================================
ALTER TABLE public.trip
ADD COLUMN IF NOT EXISTS driver_id INTEGER;

ALTER TABLE public.vehicle
ALTER COLUMN plate_number TYPE VARCHAR(20);

ALTER TABLE public.vehicle
ALTER COLUMN vehicle_type TYPE VARCHAR(50);

ALTER TABLE public.trip
ALTER COLUMN plate_number TYPE VARCHAR(20);

ALTER TABLE public.route
ALTER COLUMN route_name TYPE VARCHAR(100);

ALTER TABLE public.route
ALTER COLUMN start_location TYPE VARCHAR(100);

ALTER TABLE public.route
ALTER COLUMN end_location TYPE VARCHAR(100);

ALTER TABLE public.stop
ALTER COLUMN stop_name TYPE VARCHAR(100);

ALTER TABLE public.stop
ALTER COLUMN address TYPE VARCHAR(150);

ALTER TABLE public.driver
ALTER COLUMN driver_fullname TYPE VARCHAR(100);

ALTER TABLE public.passenger
ALTER COLUMN pass_fullname TYPE VARCHAR(100);

ALTER TABLE public.registration
ALTER COLUMN status TYPE VARCHAR(30);

-- ========================================================
-- 3) העתקת נתונים מ-other_db_temp
-- מזהי מפתחות (IDs) מסוג מספר שלם מהמערכת השנייה מקבלים תוספת של 10000 כדי למנוע התנגשויות.
-- ========================================================

-- 3.1 רכבים (vehicle)
INSERT INTO public.vehicle (plate_number, vehicle_type, capacity)
SELECT src.plate_number, src.vehicle_type, src.capacity
FROM dblink(
    'host=localhost port=5432 dbname=other_db_temp user=efrat',
    'SELECT plate_number, vehicle_type, capacity FROM public.vehicle'
) AS src(
    plate_number VARCHAR,
    vehicle_type VARCHAR,
    capacity INTEGER
)
WHERE NOT EXISTS (
    SELECT 1
    FROM public.vehicle v
    WHERE v.plate_number = src.plate_number
);

-- 3.2 מסלולים (route)
INSERT INTO public.route (
    route_id,
    route_name,
    start_location,
    end_location,
    estimated_duration_minutes,
    total_distance_km,
    created_date,
    region_id
)
SELECT
    src.route_id + 10000,
    src.route_name,
    'Unknown',
    'Unknown',
    1,
    1,
    CURRENT_DATE,
    (SELECT MIN(region_id) FROM public.region)
FROM dblink(
    'host=localhost port=5432 dbname=other_db_temp user=efrat',
    'SELECT route_id, route_name FROM public.route'
) AS src(
    route_id INTEGER,
    route_name VARCHAR
)
WHERE NOT EXISTS (
    SELECT 1
    FROM public.route r
    WHERE r.route_id = src.route_id + 10000
);

-- 3.3 תחנות (stop)
INSERT INTO public.stop (
    stop_id,
    stop_name,
    address,
    latitude,
    longitude,
    site_name
)
SELECT
    src.stop_id + 10000,
    src.stop_name,
    'Unknown',
    0,
    0,
    (SELECT MIN(site_name) FROM public.site)
FROM dblink(
    'host=localhost port=5432 dbname=other_db_temp user=efrat',
    'SELECT stop_id, stop_name FROM public.stop'
) AS src(
    stop_id INTEGER,
    stop_name VARCHAR
)
WHERE NOT EXISTS (
    SELECT 1
    FROM public.stop s
    WHERE s.stop_id = src.stop_id + 10000
);

-- 3.4 נהגים (driver)
INSERT INTO public.driver (
    driver_id,
    driver_fullname,
    phone,
    license_number
)
SELECT
    src.driver_id + 10000,
    src.driver_fullname,
    NULL,
    NULL
FROM dblink(
    'host=localhost port=5432 dbname=other_db_temp user=efrat',
    'SELECT driver_id, driver_fullname FROM public.driver'
) AS src(
    driver_id INTEGER,
    driver_fullname VARCHAR
)
WHERE NOT EXISTS (
    SELECT 1
    FROM public.driver d
    WHERE d.driver_id = src.driver_id + 10000
);

-- 3.5 נוסעים (passenger)
INSERT INTO public.passenger (
    pass_id,
    pass_fullname,
    phone
)
SELECT
    src.pass_id + 10000,
    src.pass_fullname,
    NULL
FROM dblink(
    'host=localhost port=5432 dbname=other_db_temp user=efrat',
    'SELECT pass_id, pass_fullname FROM public.passenger'
) AS src(
    pass_id INTEGER,
    pass_fullname VARCHAR
)
WHERE NOT EXISTS (
    SELECT 1
    FROM public.passenger p
    WHERE p.pass_id = src.pass_id + 10000
);

-- 3.6 includes
INSERT INTO public.includes (
    route_id,
    stop_id
)
SELECT
    src.route_id + 10000,
    src.stop_id + 10000
FROM dblink(
    'host=localhost port=5432 dbname=other_db_temp user=efrat',
    'SELECT route_id, stop_id FROM public.includes'
) AS src(
    route_id INTEGER,
    stop_id INTEGER
)
WHERE NOT EXISTS (
    SELECT 1
    FROM public.includes i
    WHERE i.route_id = src.route_id + 10000
      AND i.stop_id = src.stop_id + 10000
);

-- 3.7 סדר תחנות במסלול (route_stop)
INSERT INTO public.route_stop (
    stop_order,
    estimated_arrival_time,
    route_id,
    stop_id
)
SELECT
    ROW_NUMBER() OVER (
        PARTITION BY src.route_id
        ORDER BY src.stop_id
    ) AS stop_order,
    '00:00',
    src.route_id + 10000,
    src.stop_id + 10000
FROM dblink(
    'host=localhost port=5432 dbname=other_db_temp user=efrat',
    'SELECT route_id, stop_id FROM public.includes'
) AS src(
    route_id INTEGER,
    stop_id INTEGER
)
WHERE NOT EXISTS (
    SELECT 1
    FROM public.route_stop rs
    WHERE rs.route_id = src.route_id + 10000
      AND rs.stop_id = src.stop_id + 10000
);

-- 3.8 נסיעות (trip)
INSERT INTO public.trip (
    trip_id,
    trip_date,
    departure_time,
    available_seats,
    route_id,
    plate_number,
    driver_id
)
SELECT
    src.trip_id + 10000,
    src.trip_date,
    LEFT(src.departure_time::TEXT, 5),
    src.available_seats,
    src.route_id + 10000,
    src.plate_number,
    src.driver_id + 10000
FROM dblink(
    'host=localhost port=5432 dbname=other_db_temp user=efrat',
    'SELECT trip_id, trip_date, departure_time, available_seats, route_id, plate_number, driver_id FROM public.trip'
) AS src(
    trip_id INTEGER,
    trip_date DATE,
    departure_time TIME,
    available_seats INTEGER,
    route_id INTEGER,
    plate_number VARCHAR,
    driver_id INTEGER
)
WHERE NOT EXISTS (
    SELECT 1
    FROM public.trip t
    WHERE t.trip_id = src.trip_id + 10000
);

-- 3.9 הרשמות (registration)
INSERT INTO public.registration (
    reg_id,
    status,
    pass_id,
    trip_id,
    boarding_stop_id,
    dropoff_stop_id
)
SELECT
    src.reg_id + 10000,
    src.status,
    src.pass_id + 10000,
    src.trip_id + 10000,
    src.boarding_stop_id + 10000,
    src.dropoff_stop_id + 10000
FROM dblink(
    'host=localhost port=5432 dbname=other_db_temp user=efrat',
    'SELECT reg_id, status, pass_id, trip_id, boarding_stop_id, dropoff_stop_id FROM public.registration'
) AS src(
    reg_id INTEGER,
    status VARCHAR,
    pass_id INTEGER,
    trip_id INTEGER,
    boarding_stop_id INTEGER,
    dropoff_stop_id INTEGER
)
WHERE NOT EXISTS (
    SELECT 1
    FROM public.registration r
    WHERE r.reg_id = src.reg_id + 10000
)
ON CONFLICT (reg_id) DO NOTHING;

-- ========================================================
-- 4) הוספה או ריענון של מפתחות זרים (Foreign Keys)
-- ========================================================
ALTER TABLE public.trip
DROP CONSTRAINT IF EXISTS fk_trip_driver;

ALTER TABLE public.trip
ADD CONSTRAINT fk_trip_driver
FOREIGN KEY (driver_id)
REFERENCES public.driver(driver_id);

ALTER TABLE public.registration
DROP CONSTRAINT IF EXISTS fk_registration_passenger;

ALTER TABLE public.registration
ADD CONSTRAINT fk_registration_passenger
FOREIGN KEY (pass_id)
REFERENCES public.passenger(pass_id);

ALTER TABLE public.registration
DROP CONSTRAINT IF EXISTS fk_registration_trip;

ALTER TABLE public.registration
ADD CONSTRAINT fk_registration_trip
FOREIGN KEY (trip_id)
REFERENCES public.trip(trip_id);

ALTER TABLE public.registration
DROP CONSTRAINT IF EXISTS fk_registration_boarding_stop;

ALTER TABLE public.registration
ADD CONSTRAINT fk_registration_boarding_stop
FOREIGN KEY (boarding_stop_id)
REFERENCES public.stop(stop_id);

ALTER TABLE public.registration
DROP CONSTRAINT IF EXISTS fk_registration_dropoff_stop;

ALTER TABLE public.registration
ADD CONSTRAINT fk_registration_dropoff_stop
FOREIGN KEY (dropoff_stop_id)
REFERENCES public.stop(stop_id);

ALTER TABLE public.includes
DROP CONSTRAINT IF EXISTS fk_includes_route;

ALTER TABLE public.includes
ADD CONSTRAINT fk_includes_route
FOREIGN KEY (route_id)
REFERENCES public.route(route_id);

ALTER TABLE public.includes
DROP CONSTRAINT IF EXISTS fk_includes_stop;

ALTER TABLE public.includes
ADD CONSTRAINT fk_includes_stop
FOREIGN KEY (stop_id)
REFERENCES public.stop(stop_id);

COMMIT;

-- ========================================================
-- 5) בדיקה סופית של ספירת שורות בכל טבלה
-- ========================================================
SELECT 'region' AS table_name, COUNT(*) FROM public.region
UNION ALL
SELECT 'site', COUNT(*) FROM public.site
UNION ALL
SELECT 'route', COUNT(*) FROM public.route
UNION ALL
SELECT 'stop', COUNT(*) FROM public.stop
UNION ALL
SELECT 'trip', COUNT(*) FROM public.trip
UNION ALL
SELECT 'vehicle', COUNT(*) FROM public.vehicle
UNION ALL
SELECT 'driver', COUNT(*) FROM public.driver
UNION ALL
SELECT 'passenger', COUNT(*) FROM public.passenger
UNION ALL
SELECT 'registration', COUNT(*) FROM public.registration
UNION ALL
SELECT 'includes', COUNT(*) FROM public.includes
UNION ALL
SELECT 'route_stop', COUNT(*) FROM public.route_stop;
