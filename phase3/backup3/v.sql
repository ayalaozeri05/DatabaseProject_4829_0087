-- ========================================================
-- Views.sql - Stage C Views
-- ========================================================

-- ========================================================
-- View 1: Original department view
-- Routes, regions, and number of stops per route
-- ========================================================

CREATE OR REPLACE VIEW view_route_summary AS
SELECT
    r.route_id,
    r.route_name,
    r.start_location,
    r.end_location,
    r.total_distance_km,
    r.estimated_duration_minutes,
    reg.regio_name,
    reg.terrain_type,
    COUNT(rs.stop_id) AS total_stops
FROM public.route r
JOIN public.region reg
    ON r.region_id = reg.region_id
LEFT JOIN public.route_stop rs
    ON r.route_id = rs.route_id
GROUP BY
    r.route_id,
    r.route_name,
    r.start_location,
    r.end_location,
    r.total_distance_km,
    r.estimated_duration_minutes,
    reg.regio_name,
    reg.terrain_type;

-- Query 1 on View 1:
-- Routes with more than 2 stops
SELECT *
FROM view_route_summary
WHERE total_stops > 2
ORDER BY total_stops DESC;

-- Query 2 on View 1:
-- Average number of stops per region
SELECT
    regio_name,
    AVG(total_stops) AS avg_stops_per_route
FROM view_route_summary
GROUP BY regio_name
ORDER BY avg_stops_per_route DESC;


-- ========================================================
-- View 2: Second department view
-- Passenger registrations with trip and driver details
-- ========================================================

CREATE OR REPLACE VIEW view_passenger_trip_details AS
SELECT
    p.pass_id,
    p.pass_fullname,
    p.phone,
    reg.reg_id,
    reg.status,
    t.trip_id,
    t.trip_date,
    t.departure_time,
    t.available_seats,
    d.driver_id,
    d.driver_fullname,
    t.plate_number
FROM public.registration reg
JOIN public.passenger p
    ON reg.pass_id = p.pass_id
JOIN public.trip t
    ON reg.trip_id = t.trip_id
LEFT JOIN public.driver d
    ON t.driver_id = d.driver_id;

-- Query 1 on View 2:
-- Approved registrations only
SELECT *
FROM view_passenger_trip_details
WHERE status = 'Confirmed'
ORDER BY trip_date, departure_time;

-- Query 2 on View 2:
-- Number of registrations per passenger
SELECT
    pass_fullname,
    COUNT(reg_id) AS total_registrations
FROM view_passenger_trip_details
GROUP BY pass_fullname
ORDER BY total_registrations DESC;