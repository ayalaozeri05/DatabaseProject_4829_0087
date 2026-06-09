-- ==========================================
-- פונקציה: calculate_trip_occupancy
-- תיאור: מקבלת מזהה נסיעה ומחזירה מידע מפורט על תפוסת הנסיעה:
--        מזהה נסיעה, קיבולת הרכב, מקומות פנויים, כמות נוסעים רשומים (שאינם מבוטלים),
--        אחוז התפוסה והערכת סטטוס מילולית (FULL / ALMOST FULL / AVAILABLE).
-- ==========================================

-- מחיקת הפונקציה במידה והיא קיימת
DROP FUNCTION IF EXISTS calculate_trip_occupancy(INT);

CREATE OR REPLACE FUNCTION calculate_trip_occupancy(p_trip_id INT)
RETURNS TABLE(
    trip_id INT,
    capacity INT,
    available_seats INT,
    registered_passengers INT,
    occupancy_percent NUMERIC,
    status_text VARCHAR
) AS $$
DECLARE
    v_capacity INT;
    v_available_seats INT;
    v_registered_count INT;
    v_occupancy_pct NUMERIC;
    v_status VARCHAR(20);
    v_trip_exists BOOLEAN;
BEGIN
    -- בדיקה האם הנסיעה קיימת בבסיס הנתונים
    SELECT EXISTS(SELECT 1 FROM trip WHERE trip.trip_id = p_trip_id) INTO v_trip_exists;
    IF NOT v_trip_exists THEN
        RAISE EXCEPTION 'שגיאה: נסיעה עם מזהה % אינה קיימת במערכת.', p_trip_id;
    END IF;

    -- שליפת קיבולת הרכב ומספר המושבים הפנויים
    SELECT v.capacity, t.available_seats
    INTO v_capacity, v_available_seats
    FROM trip t
    JOIN vehicle v ON t.plate_number = v.plate_number
    WHERE t.trip_id = p_trip_id;

    -- ספירת הנוסעים הרשומים לנסיעה שאינם בסטטוס מבוטל ('Cancelled')
    SELECT COUNT(*)::INT
    INTO v_registered_count
    FROM registration r
    WHERE r.trip_id = p_trip_id
      AND (r.status IS NULL OR r.status <> 'Cancelled');

    -- חישוב אחוז התפוסה (מניעת חלוקה באפס במידה והקיבולת לא הוגדרה כראוי)
    IF v_capacity > 0 THEN
        v_occupancy_pct := ROUND((v_registered_count::NUMERIC / v_capacity::NUMERIC) * 100, 2);
    ELSE
        v_occupancy_pct := 0.00;
    END IF;

    -- קביעת הסטטוס המילולי לפי אחוז התפוסה ומקומות פנויים
    IF v_occupancy_pct >= 100.00 OR v_available_seats = 0 THEN
        v_status := 'FULL';
    ELSIF v_occupancy_pct >= 80.00 THEN
        v_status := 'ALMOST FULL';
    ELSE
        v_status := 'AVAILABLE';
    END IF;

    -- החזרת השורה כתוצאה של הטבלה
    RETURN QUERY
    SELECT p_trip_id, v_capacity, v_available_seats, v_registered_count, v_occupancy_pct, v_status;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- הרצת בדיקה לדוגמה
-- ==========================================
-- נבצע שליפה עבור נסיעה קיימת (שולף נסיעה ראשונה לצורך הדגמה)
SELECT * FROM calculate_trip_occupancy((SELECT trip_id FROM trip LIMIT 1));
