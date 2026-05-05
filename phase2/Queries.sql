-- =========================
-- Queries.sql
-- שלב ב - TransRoute Planner
-- =========================

-- SELECT 1A: Dashboard - מסלולים + אזור + מספר תחנות
SELECT
    r.route_id,
    r.route_name,
    reg.regio_name,
    r.estimated_duration_minutes,
    r.total_distance_km,
    COUNT(rs.stop_id) AS total_stops
FROM route r
JOIN region reg ON r.region_id = reg.region_id
LEFT JOIN route_stop rs ON r.route_id = rs.route_id
GROUP BY r.route_id, r.route_name, reg.regio_name, r.estimated_duration_minutes, r.total_distance_km
ORDER BY r.route_id;


-- SELECT 1B: אותה שאילתא עם Subquery
SELECT
    r.route_id,
    r.route_name,
    reg.regio_name,
    r.estimated_duration_minutes,
    r.total_distance_km,
    (
        SELECT COUNT(*)
        FROM route_stop rs
        WHERE rs.route_id = r.route_id
    ) AS total_stops
FROM route r
JOIN region reg ON r.region_id = reg.region_id
ORDER BY r.route_id;


-- SELECT 2: Route Details - תחנות במסלול לפי סדר
SELECT
    r.route_name,
    rs.stop_order,
    s.stop_name,
    s.address,
    rs.estimated_arrival_time,
    si.site_name,
    si.site_type
FROM route_stop rs
JOIN route r ON rs.route_id = r.route_id
JOIN stop s ON rs.stop_id = s.stop_id
JOIN site si ON s.site_name = si.site_name
WHERE r.route_id = 1
ORDER BY rs.stop_order;


-- SELECT 3A: Schedule - נסיעות לפי תאריך
SELECT
    t.trip_id,
    t.trip_date,
    EXTRACT(YEAR FROM t.trip_date) AS trip_year,
    EXTRACT(MONTH FROM t.trip_date) AS trip_month,
    EXTRACT(DAY FROM t.trip_date) AS trip_day,
    t.departure_time,
    r.route_name,
    v.plate_number,
    v.vehicle_type,
    t.available_seats
FROM trip t
JOIN route r ON t.route_id = r.route_id
JOIN vehicle v ON t.plate_number = v.plate_number
WHERE t.trip_date BETWEEN DATE '2025-01-01' AND DATE '2025-12-31'
ORDER BY t.trip_date, t.departure_time;


-- SELECT 3B: אותה שאילתא עם EXISTS
SELECT
    t.trip_id,
    t.trip_date,
    t.departure_time,
    t.available_seats,
    t.route_id,
    t.plate_number
FROM trip t
WHERE EXISTS (
    SELECT 1
    FROM route r
    WHERE r.route_id = t.route_id
)
AND t.trip_date BETWEEN DATE '2025-01-01' AND DATE '2025-12-31'
ORDER BY t.trip_date, t.departure_time;


-- SELECT 4: Trip Summary - תפוסת נסיעה
SELECT
    t.trip_id,
    r.route_name,
    t.trip_date,
    t.departure_time,
    v.plate_number,
    v.vehicle_type,
    v.capacity,
    t.available_seats,
    (v.capacity - t.available_seats) AS occupied_seats,
    ROUND(((v.capacity - t.available_seats)::numeric / v.capacity) * 100, 2) AS occupancy_percent
FROM trip t
JOIN route r ON t.route_id = r.route_id
JOIN vehicle v ON t.plate_number = v.plate_number
WHERE t.trip_id = 1;


-- SELECT 5A: כמות מסלולים לפי אזור
SELECT
    reg.region_id,
    reg.regio_name,
    reg.terrain_type,
    COUNT(r.route_id) AS total_routes
FROM region reg
LEFT JOIN route r ON reg.region_id = r.region_id
GROUP BY reg.region_id, reg.regio_name, reg.terrain_type
ORDER BY total_routes DESC;


-- SELECT 5B: אותה שאילתא עם Subquery
SELECT
    reg.region_id,
    reg.regio_name,
    reg.terrain_type,
    (
        SELECT COUNT(*)
        FROM route r
        WHERE r.region_id = reg.region_id
    ) AS total_routes
FROM region reg
ORDER BY total_routes DESC;


-- SELECT 6: ממוצע זמן ומרחק לפי אזור
SELECT
    reg.regio_name,
    reg.terrain_type,
    COUNT(r.route_id) AS routes_count,
    ROUND(AVG(r.estimated_duration_minutes), 2) AS avg_duration,
    ROUND(AVG(r.total_distance_km)::numeric, 2) AS avg_distance
FROM region reg
JOIN route r ON reg.region_id = r.region_id
GROUP BY reg.regio_name, reg.terrain_type
HAVING COUNT(r.route_id) > 0
ORDER BY avg_duration DESC;


-- SELECT 7A: רכבים הכי פעילים
SELECT
    v.plate_number,
    v.vehicle_type,
    v.capacity,
    COUNT(t.trip_id) AS total_trips
FROM vehicle v
JOIN trip t ON v.plate_number = t.plate_number
GROUP BY v.plate_number, v.vehicle_type, v.capacity
ORDER BY total_trips DESC
LIMIT 10;


-- SELECT 7B: רכבים פעילים עם IN
SELECT
    v.plate_number,
    v.vehicle_type,
    v.capacity
FROM vehicle v
WHERE v.plate_number IN (
    SELECT t.plate_number
    FROM trip t
    GROUP BY t.plate_number
    HAVING COUNT(*) > 5
)
ORDER BY v.plate_number;


-- SELECT 8: ימים וחודשים עמוסים בנסיעות
SELECT
    EXTRACT(YEAR FROM trip_date) AS trip_year,
    EXTRACT(MONTH FROM trip_date) AS trip_month,
    EXTRACT(DAY FROM trip_date) AS trip_day,
    COUNT(*) AS total_trips
FROM trip
GROUP BY
    EXTRACT(YEAR FROM trip_date),
    EXTRACT(MONTH FROM trip_date),
    EXTRACT(DAY FROM trip_date)
ORDER BY total_trips DESC;


-- =========================
-- UPDATE QUERIES
-- =========================

-- UPDATE 1: עדכון מקומות פנויים בנסיעות שעברו
UPDATE trip
SET available_seats = 0
WHERE trip_date < CURRENT_DATE
AND available_seats > 0;

-- UPDATE 2: העלאת משך מסלולים ארוכים
UPDATE route
SET estimated_duration_minutes = estimated_duration_minutes + 15
WHERE total_distance_km > 150;


-- UPDATE 3: עדכון סוג אזור לפי תיאור
UPDATE region
SET terrain_type = 'Tourism'
WHERE description LIKE '%תיירות%';


-- =========================
-- DELETE QUERIES
-- =========================

-- DELETE 1: מחיקת שיוך אזור-רכב בלי נסיעות בפועל
DELETE FROM region_vehicle
WHERE region_id IN (
    SELECT region_id
    FROM region
    LIMIT 2
);


-- DELETE 2: מחיקת נסיעות ללא מקומות פנויים מתאריך עבר
DELETE FROM trip
WHERE trip_date < CURRENT_DATE
AND available_seats = 0;


-- DELETE 3: מחיקת תחנות שלא משויכות לשום מסלול
DELETE FROM route_stop
WHERE stop_id IN (1, 2);