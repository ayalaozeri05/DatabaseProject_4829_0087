-- ========================================================
-- מבטים (Views) לשלב ג'
-- ========================================================

-- --------------------------------------------------------
-- מבט 1: מנקודת המבט של האגף המקורי (ניהול נסיעות ומסלולים)
-- המבט מציג נסיעות מתוזמנות כולל פרטי המסלול, הנהג והרכב
-- --------------------------------------------------------
CREATE OR REPLACE VIEW schedule_trip_view AS
SELECT
    t.trip_id,
    t.trip_date,
    t.departure_time,
    t.available_seats,
    r.route_name,
    r.start_location,
    r.end_location,
    d.driver_fullname,
    v.plate_number,
    v.vehicle_type,
    v.capacity
FROM trip_5626 t
JOIN route_5626 r ON t.route_id = r.route_id
JOIN driver d ON t.driver_id = d.driver_id
JOIN vehicle_5626 v ON t.plate_number = v.plate_number;

-- שאילתא 1 על schedule_trip_view: נסיעות קרובות לפי תאריך ושעה
SELECT
    trip_id,
    trip_date,
    departure_time,
    route_name,
    driver_fullname,
    plate_number,
    vehicle_type
FROM schedule_trip_view
WHERE trip_date >= CURRENT_DATE
ORDER BY trip_date, departure_time
LIMIT 10;

-- שאילתא 2 על schedule_trip_view: נסיעות עם מעט מקומות פנויים
SELECT
    trip_id,
    trip_date,
    departure_time,
    route_name,
    available_seats,
    driver_fullname,
    plate_number
FROM schedule_trip_view
WHERE available_seats <= 10
ORDER BY available_seats ASC;


-- --------------------------------------------------------
-- מבט 2: מנקודת המבט של האגף המקביל (ניהול נוסעים והרשמות)
-- המבט מציג פרטי נוסע, פרטי הרשמה, פרטי נסיעה, מסלול, נהג, רכב ותחנות עלייה/ירידה
-- --------------------------------------------------------
CREATE OR REPLACE VIEW passenger_trip_booking_view AS
SELECT
    p.pass_id,
    p.pass_fullname,
    p.phone,
    r.reg_id,
    r.status,
    tr.trip_id,
    tr.trip_date,
    tr.departure_time,
    tr.available_seats,
    ro.route_name,
    ro.start_location,
    ro.end_location,
    d.driver_fullname,
    d.licenseType,
    v.plate_number,
    v.vehicle_type,
    bs.stop_name AS boarding_stop,
    ds.stop_name AS dropoff_stop
FROM registration r
JOIN passenger p ON r.pass_id = p.pass_id
JOIN trip_5626 tr ON r.trip_id = tr.trip_id
JOIN route_5626 ro ON tr.route_id = ro.route_id
JOIN driver d ON tr.driver_id = d.driver_id
JOIN vehicle_5626 v ON tr.plate_number = v.plate_number
JOIN stop_5626 bs ON r.boarding_stop_id = bs.stop_id
JOIN stop_5626 ds ON r.dropoff_stop_id = ds.stop_id;

-- שאילתא 1 על passenger_trip_booking_view: כמה נוסעים רשומים לכל נסיעה
SELECT
    trip_id,
    route_name,
    trip_date,
    departure_time,
    COUNT(pass_id) AS registered_passengers
FROM passenger_trip_booking_view
GROUP BY trip_id, route_name, trip_date, departure_time
ORDER BY registered_passengers DESC;

-- שאילתא 2 על passenger_trip_booking_view: נוסעים שהשלימו נסיעה (Completed)
SELECT
    pass_fullname,
    phone,
    route_name,
    trip_date,
    departure_time,
    boarding_stop,
    dropoff_stop,
    driver_fullname,
    plate_number
FROM passenger_trip_booking_view
WHERE status = 'Completed'
ORDER BY trip_date, departure_time;
