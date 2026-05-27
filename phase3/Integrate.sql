BEGIN;

-- =========================================================
-- 1) מחיקת טבלאות כפולות/מיותרות
-- =========================================================

DROP TABLE IF EXISTS public.includes CASCADE;
DROP TABLE IF EXISTS public.region_vehicle CASCADE;

DROP TABLE IF EXISTS public.route CASCADE;
DROP TABLE IF EXISTS public.stop CASCADE;
DROP TABLE IF EXISTS public.trip CASCADE;
DROP TABLE IF EXISTS public.vehicle CASCADE;


-- =========================================================
-- 2) התאמות עמודות קיימות
-- =========================================================

ALTER TABLE public.vehicle_5626
ALTER COLUMN plate_number TYPE character varying(20);

ALTER TABLE public.trip_5626
ADD COLUMN IF NOT EXISTS driver_id integer;

ALTER TABLE public.registration
ADD COLUMN IF NOT EXISTS reg_id integer;

ALTER TABLE public.registration
ADD COLUMN IF NOT EXISTS status character varying(20);

ALTER TABLE public.registration
ADD COLUMN IF NOT EXISTS pass_id integer;

ALTER TABLE public.registration
ADD COLUMN IF NOT EXISTS trip_id integer;

ALTER TABLE public.registration
ADD COLUMN IF NOT EXISTS boarding_stop_id integer;

ALTER TABLE public.registration
ADD COLUMN IF NOT EXISTS dropoff_stop_id integer;


-- =========================================================
-- 3) הפיכת registration לישות רגילה
-- כלומר PK רק על reg_id, לא pass_id + reg_id
-- =========================================================

ALTER TABLE public.registration
DROP CONSTRAINT IF EXISTS registration_pkey;

ALTER TABLE public.registration
ADD CONSTRAINT registration_pkey
PRIMARY KEY (reg_id);


-- =========================================================
-- 4) ניקוי נתונים שבורים לפני יצירת Foreign Keys
-- =========================================================

DELETE FROM public.registration r
WHERE r.pass_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM public.passenger p
      WHERE p.pass_id = r.pass_id
  );

DELETE FROM public.registration r
WHERE r.trip_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM public.trip_5626 t
      WHERE t.trip_id = r.trip_id
  );

DELETE FROM public.registration r
WHERE r.boarding_stop_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM public.stop_5626 s
      WHERE s.stop_id = r.boarding_stop_id
  );

DELETE FROM public.registration r
WHERE r.dropoff_stop_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM public.stop_5626 s
      WHERE s.stop_id = r.dropoff_stop_id
  );

DELETE FROM public.trip_5626 t
WHERE t.route_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM public.route_5626 r
      WHERE r.route_id = t.route_id
  );

DELETE FROM public.trip_5626 t
WHERE t.plate_number IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM public.vehicle_5626 v
      WHERE v.plate_number = t.plate_number
  );

DELETE FROM public.trip_5626 t
WHERE t.driver_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM public.driver d
      WHERE d.driver_id = t.driver_id
  );

DELETE FROM public.route_stop rs
WHERE NOT EXISTS (
      SELECT 1
      FROM public.route_5626 r
      WHERE r.route_id = rs.route_id
  )
   OR NOT EXISTS (
      SELECT 1
      FROM public.stop_5626 s
      WHERE s.stop_id = rs.stop_id
  );

DELETE FROM public.stop_5626 s
WHERE s.site_name IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM public.site si
      WHERE si.site_name = s.site_name
  );

DELETE FROM public.route_5626 r
WHERE r.region_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM public.region rg
      WHERE rg.region_id = r.region_id
  );


-- =========================================================
-- 5) מחיקת Foreign Keys כפולים/ישנים
-- =========================================================

ALTER TABLE public.trip_5626
DROP CONSTRAINT IF EXISTS trip_route_id_fkey;

ALTER TABLE public.trip_5626
DROP CONSTRAINT IF EXISTS trip_plate_number_fkey;

ALTER TABLE public.route_stop
DROP CONSTRAINT IF EXISTS route_stop_route_id_fkey;

ALTER TABLE public.route_stop
DROP CONSTRAINT IF EXISTS route_stop_stop_id_fkey;

ALTER TABLE public.stop_5626
DROP CONSTRAINT IF EXISTS stop_site_name_fkey;


-- =========================================================
-- 6) יצירת Foreign Keys סופיים לפי ה-ERD המשולב
-- =========================================================

ALTER TABLE public.route_5626
DROP CONSTRAINT IF EXISTS route_region_id_fkey;

ALTER TABLE public.route_5626
ADD CONSTRAINT route_region_id_fkey
FOREIGN KEY (region_id)
REFERENCES public.region(region_id);


ALTER TABLE public.route_stop
DROP CONSTRAINT IF EXISTS fk_route_stop_route;

ALTER TABLE public.route_stop
ADD CONSTRAINT fk_route_stop_route
FOREIGN KEY (route_id)
REFERENCES public.route_5626(route_id);


ALTER TABLE public.route_stop
DROP CONSTRAINT IF EXISTS fk_route_stop_stop;

ALTER TABLE public.route_stop
ADD CONSTRAINT fk_route_stop_stop
FOREIGN KEY (stop_id)
REFERENCES public.stop_5626(stop_id);


ALTER TABLE public.stop_5626
DROP CONSTRAINT IF EXISTS fk_stop_site;

ALTER TABLE public.stop_5626
ADD CONSTRAINT fk_stop_site
FOREIGN KEY (site_name)
REFERENCES public.site(site_name);


ALTER TABLE public.trip_5626
DROP CONSTRAINT IF EXISTS fk_trip_route;

ALTER TABLE public.trip_5626
ADD CONSTRAINT fk_trip_route
FOREIGN KEY (route_id)
REFERENCES public.route_5626(route_id);


ALTER TABLE public.trip_5626
DROP CONSTRAINT IF EXISTS fk_trip_vehicle;

ALTER TABLE public.trip_5626
ADD CONSTRAINT fk_trip_vehicle
FOREIGN KEY (plate_number)
REFERENCES public.vehicle_5626(plate_number);


ALTER TABLE public.trip_5626
DROP CONSTRAINT IF EXISTS fk_trip_driver;

ALTER TABLE public.trip_5626
ADD CONSTRAINT fk_trip_driver
FOREIGN KEY (driver_id)
REFERENCES public.driver(driver_id);


ALTER TABLE public.registration
DROP CONSTRAINT IF EXISTS registration_pass_id_fkey;

ALTER TABLE public.registration
ADD CONSTRAINT registration_pass_id_fkey
FOREIGN KEY (pass_id)
REFERENCES public.passenger(pass_id);


ALTER TABLE public.registration
DROP CONSTRAINT IF EXISTS registration_trip_id_fkey;

ALTER TABLE public.registration
ADD CONSTRAINT registration_trip_id_fkey
FOREIGN KEY (trip_id)
REFERENCES public.trip_5626(trip_id);


ALTER TABLE public.registration
DROP CONSTRAINT IF EXISTS registration_boarding_stop_id_fkey;

ALTER TABLE public.registration
ADD CONSTRAINT registration_boarding_stop_id_fkey
FOREIGN KEY (boarding_stop_id)
REFERENCES public.stop_5626(stop_id);


ALTER TABLE public.registration
DROP CONSTRAINT IF EXISTS registration_dropoff_stop_id_fkey;

ALTER TABLE public.registration
ADD CONSTRAINT registration_dropoff_stop_id_fkey
FOREIGN KEY (dropoff_stop_id)
REFERENCES public.stop_5626(stop_id);


-- =========================================================
-- 7) חיזוק route_stop
-- =========================================================

ALTER TABLE public.route_stop
DROP CONSTRAINT IF EXISTS route_stop_pkey;

ALTER TABLE public.route_stop
ADD CONSTRAINT route_stop_pkey
PRIMARY KEY (route_id, stop_id);


ALTER TABLE public.route_stop
DROP CONSTRAINT IF EXISTS route_stop_route_id_stop_order_key;

ALTER TABLE public.route_stop
ADD CONSTRAINT route_stop_route_id_stop_order_key
UNIQUE (route_id, stop_order);


ALTER TABLE public.route_stop
DROP CONSTRAINT IF EXISTS route_stop_stop_order_check;

ALTER TABLE public.route_stop
ADD CONSTRAINT route_stop_stop_order_check
CHECK (stop_order > 0);


COMMIT;


-- =========================================================
-- בדיקה 1: הטבלאות שנשארו
-- =========================================================

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;


-- =========================================================
-- בדיקה 2: כל ה-Foreign Keys הסופיים
-- =========================================================

SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;


-- =========================================================
-- בדיקה 3: כל ה-Primary Keys
-- =========================================================

SELECT
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = 'public'
  AND tc.constraint_type = 'PRIMARY KEY'
ORDER BY tc.table_name, kcu.column_name;