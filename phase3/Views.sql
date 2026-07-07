-- ========================================================
-- מבטים (Views) לשלב ג'
-- ========================================================

-- מבט 1: מנקודת המבט של האגף המקורי שלנו (ניהול מסלולים ואזורים)
-- המבט מציג מידע משולב על מסלולים, האזור שאליו הם שייכים וכמות התחנות שיש בכל מסלול.
CREATE OR REPLACE VIEW view_route_summary AS
SELECT r.route_id, r.route_name, r.start_location, r.end_location,
       reg.regio_name, reg.terrain_type,
       COUNT(rs.stop_id) AS total_stops
FROM public.route_5626 r
JOIN public.region reg ON r.region_id = reg.region_id
LEFT JOIN public.route_stop rs ON r.route_id = rs.route_id
GROUP BY r.route_id, r.route_name, r.start_location, r.end_location, reg.regio_name, reg.terrain_type;

-- שאילתא 1 על מבט 1: הצגת מסלולים עם יותר מ-2 תחנות
SELECT * FROM view_route_summary WHERE total_stops > 2 ORDER BY route_id;

-- שאילתא 2 על מבט 1: חישוב ממוצע תחנות למסלול לפי כל אזור
SELECT regio_name, AVG(total_stops) AS avg_stops FROM view_route_summary GROUP BY regio_name;


-- מבט 2: מנקודת המבט של האגף החדש שקיבלנו (ניהול נוסעים, נהגים והרשמות)
-- המבט מציג את פרטי הנוסעים, סטטוס ההרשמה שלהם, ופרטי הנסיעה (תאריך ורכב משובץ).
CREATE OR REPLACE VIEW view_passenger_trip_details AS
SELECT p.pass_id, p.pass_fullname, p.phone,
       reg.status,
       t.trip_id, t.trip_date, t.plate_number
FROM public.passenger p
JOIN public.registration reg ON p.pass_id = reg.pass_id
JOIN public.trip_5626 t ON reg.trip_id = t.trip_id;

-- שאילתא 1 על מבט 2: שליפת הרשמות שאושרו בלבד
SELECT * FROM view_passenger_trip_details WHERE status = 'Confirmed' ORDER BY trip_date;

-- שאילתא 2 על מבט 2: ספירת כמות הנסיעות של כל נוסע (לנוסעים שנסעו לפחות פעם אחת)
 SELECT pass_fullname, COUNT(trip_id) AS total_trips
  FROM view_passenger_trip_details
   GROUP BY pass_fullname ORDER BY total_trips DESC;
-- מבט 3: schedule_trip_view
-- מבט מנקודת המבט של ניהול לוחות הזמנים והנסיעות.
-- המבט מציג מידע משולב על נסיעות מתוזמנות, כולל פרטי המסלול (מוצא ויעד), פרטי הנהג וסוג הרכב.
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
LEFT JOIN route_5626 r ON t.route_id = r.route_id
LEFT JOIN driver d ON t.driver_id = d.driver_id
LEFT JOIN vehicle_5626 v ON t.plate_number = v.plate_number;