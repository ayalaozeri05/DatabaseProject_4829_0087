ALTER TABLE IF EXISTS driver RENAME TO driver_5626;
ALTER TABLE IF EXISTS includes RENAME TO includes_5626;
ALTER TABLE IF EXISTS passenger RENAME TO passenger_5626;
ALTER TABLE IF EXISTS registration RENAME TO registration_5626;
ALTER TABLE IF EXISTS route RENAME TO route_5626;
ALTER TABLE IF EXISTS stop RENAME TO stop_5626;
ALTER TABLE IF EXISTS trip RENAME TO trip_5626;
ALTER TABLE IF EXISTS vehicle RENAME TO vehicle_5626;

ALTER INDEX IF EXISTS driver_pkey RENAME TO driver_5626_pkey;
ALTER INDEX IF EXISTS includes_pkey RENAME TO includes_5626_pkey;
ALTER INDEX IF EXISTS passenger_pkey RENAME TO passenger_5626_pkey;
ALTER INDEX IF EXISTS registration_pkey RENAME TO registration_5626_pkey;
ALTER INDEX IF EXISTS route_pkey RENAME TO route_5626_pkey;
ALTER INDEX IF EXISTS stop_pkey RENAME TO stop_5626_pkey;
ALTER INDEX IF EXISTS trip_pkey RENAME TO trip_5626_pkey;
ALTER INDEX IF EXISTS vehicle_pkey RENAME TO vehicle_5626_pkey;

ALTER INDEX IF EXISTS passenger_email_key RENAME TO passenger_5626_email_key;
ALTER INDEX IF EXISTS passenger_phone_key RENAME TO passenger_5626_phone_key;
ALTER INDEX IF EXISTS idx_passenger_name RENAME TO idx_passenger_5626_name;
ALTER INDEX IF EXISTS idx_reg_trip_id RENAME TO idx_reg_5626_trip_id;
ALTER INDEX IF EXISTS idx_trip_date RENAME TO idx_trip_5626_date;
ALTER INDEX IF EXISTS idx_vehicle_capacity RENAME TO idx_vehicle_5626_capacity;

ALTER TABLE public.vehicle_5626 ALTER COLUMN plate_number TYPE character varying(20);

CREATE TABLE IF NOT EXISTS public.driver (
    driver_id integer PRIMARY KEY,
    driver_fullname character varying(50) NOT NULL,
    licenseType character varying(100)
);

ALTER TABLE public.trip_5626 ADD COLUMN IF NOT EXISTS driver_id integer;
ALTER TABLE public.trip_5626 ADD CONSTRAINT fk_trip_driver FOREIGN KEY (driver_id) REFERENCES public.driver(driver_id);

CREATE TABLE IF NOT EXISTS public.passenger (
    pass_id integer PRIMARY KEY,
    pass_fullname character varying(100) NOT NULL,
    phone character varying(20),
    email character varying(100),
    sector character varying(50)
);

CREATE TABLE IF NOT EXISTS public.registration (
    reg_id integer PRIMARY KEY,
    status character varying(20),
    pass_id integer NOT NULL,
    trip_id integer NOT NULL,
    boarding_stop_id integer,
    dropoff_stop_id integer,
    CONSTRAINT fk_registration_passenger FOREIGN KEY (pass_id) REFERENCES public.passenger(pass_id),
    CONSTRAINT fk_registration_trip FOREIGN KEY (trip_id) REFERENCES public.trip_5626(trip_id),
    CONSTRAINT fk_registration_boarding_stop FOREIGN KEY (boarding_stop_id) REFERENCES public.stop_5626(stop_id),
    CONSTRAINT fk_registration_dropoff_stop FOREIGN KEY (dropoff_stop_id) REFERENCES public.stop_5626(stop_id)
);

ALTER TABLE public.trip_5626 ADD CONSTRAINT fk_trip_route FOREIGN KEY (route_id) REFERENCES public.route_5626(route_id);
ALTER TABLE public.trip_5626 ADD CONSTRAINT fk_trip_vehicle FOREIGN KEY (plate_number) REFERENCES public.vehicle_5626(plate_number);
ALTER TABLE public.route_stop ADD CONSTRAINT fk_route_stop_route FOREIGN KEY (route_id) REFERENCES public.route_5626(route_id);
ALTER TABLE public.route_stop ADD CONSTRAINT fk_route_stop_stop FOREIGN KEY (stop_id) REFERENCES public.stop_5626(stop_id);
ALTER TABLE public.stop_5626 ADD CONSTRAINT fk_stop_site FOREIGN KEY (site_name) REFERENCES public.site(site_name);

BEGIN;
DROP TABLE IF EXISTS public.includes CASCADE;
DROP TABLE IF EXISTS public.region_vehicle CASCADE;
DROP TABLE IF EXISTS public.route CASCADE;
DROP TABLE IF EXISTS public.stop CASCADE;
DROP TABLE IF EXISTS public.trip CASCADE;
DROP TABLE IF EXISTS public.vehicle CASCADE;
COMMIT;
