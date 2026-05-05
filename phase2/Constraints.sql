-- =========================
-- Constraints.sql
-- שלב ב
-- =========================

-- 1. קיבולת רכב חייבת להיות חיובית
ALTER TABLE vehicle
ADD CONSTRAINT chk_vehicle_capacity_positive
CHECK (capacity > 0);

-- בדיקת שגיאה
INSERT INTO vehicle (plate_number, vehicle_type, capacity)
VALUES ('9999999', 'Bus', -5);


-- 2. מספר מקומות פנויים לא יכול להיות שלילי
ALTER TABLE trip
ADD CONSTRAINT chk_trip_available_seats_non_negative
CHECK (available_seats >= 0);

-- בדיקת שגיאה
INSERT INTO trip (trip_id, trip_date, departure_time, available_seats, route_id, plate_number)
VALUES (999999, '2025-05-01', '08:00', -3, 1, '3007919');


-- 3. מרחק מסלול חייב להיות גדול מ־0
ALTER TABLE route
ADD CONSTRAINT chk_route_distance_positive
CHECK (total_distance_km > 0);

-- בדיקת שגיאה
INSERT INTO route
(route_id, route_name, start_location, end_location, estimated_duration_minutes, total_distance_km, created_date, region_id)
VALUES (999999, 'Invalid Route', 'A', 'B', 60, -10, '2025-01-01', 1);