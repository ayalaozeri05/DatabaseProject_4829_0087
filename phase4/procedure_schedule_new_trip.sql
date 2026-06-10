-- ==========================================
-- פרוצדורה: schedule_new_trip
-- תיאור: מדמה את מסך Schedule New Trip. מקבלת מזהי נסיעה, מסלול, תאריך,
--        שעת יציאה, מספר נוסעים צפויים, מספר רישוי רכב ומזהה נהג.
--        מבצעת בדיקות תקינות ומכניסה נסיעה חדשה עם מושבים פנויים מחושבים.
-- ==========================================

-- מחיקת הפרוצדורה במידה והיא קיימת
DROP PROCEDURE IF EXISTS schedule_new_trip(INT, INT, DATE, VARCHAR(5), INT, VARCHAR(15), INT);
DROP PROCEDURE IF EXISTS schedule_new_trip(INT, INT, DATE, VARCHAR, INT, VARCHAR, INT);

CREATE OR REPLACE PROCEDURE schedule_new_trip(
    p_trip_id INT,
    p_route_id INT,
    p_trip_date DATE,
    p_departure_time VARCHAR,
    p_expected_passengers INT,
    p_plate_number VARCHAR,
    p_driver_id INT
) AS $$
DECLARE
    r_route RECORD;
    r_vehicle RECORD;
    r_driver RECORD;
    v_available_seats INT;
BEGIN
    -- 1. בדיקת קיום המסלול ושמירת רשומת המסלול לתוך RECORD
    SELECT * INTO r_route FROM route WHERE route_id = p_route_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'שגיאה: המסלול עם מזהה % אינו קים במערכת.', p_route_id;
    END IF;

    -- 2. בדיקת קיום הרכב ושמירת רשומת הרכב לתוך RECORD
    SELECT * INTO r_vehicle FROM vehicle WHERE plate_number = p_plate_number;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'שגיאה: הרכב עם מספר רישוי % אינו קיים במערכת.', p_plate_number;
    END IF;

    -- 3. בדיקת קיום הנהג ושמירת רשומת הנהג לתוך RECORD
    SELECT * INTO r_driver FROM driver WHERE driver_id = p_driver_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'שגיאה: הנהג עם מזהה % אינו קיים במערכת.', p_driver_id;
    END IF;

    -- 4. בדיקת תקינות נוסעים צפויים לעומת קיבולת הרכב
    IF p_expected_passengers > r_vehicle.capacity THEN
        RAISE EXCEPTION 'שגיאה: מספר הנוסעים הצפוי (%) גדול מקיבולת הרכב (%).', 
            p_expected_passengers, r_vehicle.capacity;
    END IF;

    IF p_expected_passengers < 0 THEN
        RAISE EXCEPTION 'שגיאה: מספר הנוסעים הצפוי אינו יכול להיות שלילי.';
    END IF;

    -- חישוב מושבים פנויים התחלתיים
    v_available_seats := r_vehicle.capacity - p_expected_passengers;

    -- 5. הכנסת הנסיעה החדשה לטבלה
    INSERT INTO trip (trip_id, trip_date, departure_time, available_seats, route_id, plate_number, driver_id)
    VALUES (p_trip_id, p_trip_date, p_departure_time, v_available_seats, p_route_id, p_plate_number, p_driver_id);

    RAISE NOTICE 'הנסיעה % נוספה בהצלחה! מסלול: %, רכב: %, נהג: %, מקומות פנויים התחלתיים: %.', 
        p_trip_id, r_route.route_name, p_plate_number, r_driver.driver_fullname, v_available_seats;

EXCEPTION
    WHEN UNIQUE_VIOLATION THEN
        RAISE EXCEPTION 'שגיאה: קיים כבר מפתח נסיעה כפול (%) במערכת.', p_trip_id;
    WHEN OTHERS THEN
        RAISE EXCEPTION 'שגיאה במהלך זימון הנסיעה החדשה: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- הרצת בדיקה לדוגמה (ללא טרנזקציה על מנת לשמור על הפרוצדורה בבסיס הנתונים)
-- ==========================================
-- ניקוי מקדים של מפתח הבדיקה כדי למנוע שגיאות הרצה חוזרת
DELETE FROM trip WHERE trip_id = 99988;

DO $$
DECLARE
    v_route_id INT;
    v_plate VARCHAR(20);
    v_driver_id INT;
BEGIN
    -- שליפת ערכים תקינים מתוך בסיס הנתונים לצורך הרצת המודל
    SELECT route_id INTO v_route_id FROM route LIMIT 1;
    SELECT plate_number INTO v_plate FROM vehicle LIMIT 1;
    SELECT driver_id INTO v_driver_id FROM driver LIMIT 1;

    -- קריאה לפרוצדורה עם מזהה זמני 99988
    IF v_route_id IS NOT NULL AND v_plate IS NOT NULL AND v_driver_id IS NOT NULL THEN
        CALL schedule_new_trip(
            99988, 
            v_route_id, 
            (CURRENT_DATE + 5)::DATE, 
            '10:00'::VARCHAR, 
            3, 
            v_plate::VARCHAR, 
            v_driver_id
        );
    END IF;
END;
$$;

-- בדיקה שהנסיעה אכן נוספה לטבלת הנסיעות
SELECT * FROM trip WHERE trip_id = 99988;

-- ניקוי נתוני הבדיקה בלבד (משאיר את הפרוצדורה קיימת בבסיס הנתונים)
DELETE FROM trip WHERE trip_id = 99988;

