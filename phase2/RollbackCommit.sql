-- =========================
-- RollbackCommit.sql
-- שלב ב
-- =========================

-- =========================
-- דוגמה 1: ROLLBACK
-- =========================

-- מצב לפני
SELECT trip_id, available_seats
FROM trip
WHERE trip_id = 1;

BEGIN;

UPDATE trip
SET available_seats = available_seats - 1
WHERE trip_id = 1;

-- מצב אחרי עדכון
SELECT trip_id, available_seats
FROM trip
WHERE trip_id = 1;

ROLLBACK;

-- מצב אחרי rollback
SELECT trip_id, available_seats
FROM trip
WHERE trip_id = 1;


-- =========================
-- דוגמה 2: COMMIT
-- =========================

-- מצב לפני
SELECT route_id, estimated_duration_minutes
FROM route
WHERE route_id = 1;

BEGIN;

UPDATE route
SET estimated_duration_minutes = estimated_duration_minutes + 10
WHERE route_id = 1;

-- מצב אחרי עדכון
SELECT route_id, estimated_duration_minutes
FROM route
WHERE route_id = 1;

COMMIT;

-- מצב אחרי commit
SELECT route_id, estimated_duration_minutes
FROM route
WHERE route_id = 1;