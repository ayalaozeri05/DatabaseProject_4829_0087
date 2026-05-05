-- =========================
-- Index.sql
-- =========================

-- בדיקת זמן לפני אינדקס
EXPLAIN ANALYZE
SELECT *
FROM trip
WHERE trip_date = '2025-05-01';


-- אינדקס 1: על תאריך נסיעה
CREATE INDEX idx_trip_date
ON trip(trip_date);


-- בדיקה אחרי אינדקס
EXPLAIN ANALYZE
SELECT *
FROM trip
WHERE trip_date = '2025-05-01';



-- אינדקס 2: על route_id
EXPLAIN ANALYZE
SELECT *
FROM route_stop
WHERE route_id = 10;

CREATE INDEX idx_route_stop_route
ON route_stop(route_id);

EXPLAIN ANALYZE
SELECT *
FROM route_stop
WHERE route_id = 10;



-- אינדקס 3: על region_id
EXPLAIN ANALYZE
SELECT *
FROM route
WHERE region_id = 5;

CREATE INDEX idx_route_region
ON route(region_id);

EXPLAIN ANALYZE
SELECT *
FROM route
WHERE region_id = 5;