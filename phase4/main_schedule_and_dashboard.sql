-- ==========================================
-- תוכנית ראשית 1: main_schedule_and_dashboard
-- תיאור: יוצרת את הפונקציה והפרוצדורה הנדרשות בבסיס הנתונים (מחוץ לטרנזקציה)
--        ולאחר מכן מדגימה זימון נסיעה חדשה והצגת נתוני דשבורד מסלולים.
--        התוכנית מריצה את הבדיקה בתוך טרנזקציה ומבצעת בסופה ROLLBACK.
-- ==========================================

-- ==========================================
-- 1. יצירת הפונקציה get_route_dashboard
-- ==========================================
DROP FUNCTION IF EXISTS get_route_dashboard();

CREATE OR REPLACE FUNCTION get_route_dashboard()
RETURNS refcursor AS $$
DECLARE
    r_cursor refcursor := 'route_dashboard_cursor';
    route_exists BOOLEAN;
BEGIN
    -- בדיקה האם קיימים מסלולים כלשהם במערכת
    SELECT EXISTS(SELECT 1 FROM route) INTO route_exists;
    IF NOT route_exists THEN
        RAISE NOTICE 'שים לב: לא נמצאו מסלולים בבסיס הנתונים.';
    END IF;

    -- פתיחת ה-Cursor עבור השאילתה המורכבת
    OPEN r_cursor FOR
        SELECT 
            r.route_id, 
            r.route_name, 
            reg.regio_name AS region_name, 
            r.total_distance_km, 
            r.estimated_duration_minutes, 
            COALESCE(rs.stop_count, 0)::INT AS stop_count, 
            COALESCE(t.future_trip_count, 0)::INT AS future_trip_count
        FROM route r
        LEFT JOIN region reg ON r.region_id = reg.region_id
        LEFT JOIN (
            -- חישוב כמות התחנות לכל מסלול
            SELECT route_id, COUNT(stop_id) AS stop_count
            FROM route_stop
            GROUP BY route_id
        ) rs ON r.route_id = rs.route_id
        LEFT JOIN (
            -- חישוב כמות הנסיעות העתידיות
            SELECT route_id, COUNT(trip_id) AS future_trip_count
            FROM trip
            WHERE trip_date >= CURRENT_DATE
            GROUP BY route_id
        ) t ON r.route_id = t.route_id
        ORDER BY r.route_id;
        
    RETURN r_cursor;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'שגיאה במהלך שליפת נתוני הדשבורד: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;


-- ==========================================
-- 2. יצירת הפרוצדורה schedule_new_trip
-- ==========================================
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
    -- בדיקת קיום המסלול
    SELECT * INTO r_route FROM route WHERE route_id = p_route_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'שגיאה: המסלול עם מזהה % אינו קיים במערכת.', p_route_id;
    END IF;

    -- בדיקת קיום הרכב
    SELECT * INTO r_vehicle FROM vehicle WHERE plate_number = p_plate_number;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'שגיאה: הרכב עם מספר רישוי % אינו קיים במערכת.', p_plate_number;
    END IF;

    -- בדיקת קיום הנהג
    SELECT * INTO r_driver FROM driver WHERE driver_id = p_driver_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'שגיאה: הנהג עם מזהה % אינו קיים במערכת.', p_driver_id;
    END IF;

    -- בדיקת תקינות נוסעים צפויים לעומת קיבולת הרכב
    IF p_expected_passengers > r_vehicle.capacity THEN
        RAISE EXCEPTION 'שגיאה: מספר הנוסעים הצפוי (%) גדול מקיבולת הרכב (%).', 
            p_expected_passengers, r_vehicle.capacity;
    END IF;

    IF p_expected_passengers < 0 THEN
        RAISE EXCEPTION 'שגיאה: מספר הנוסעים הצפוי אינו יכול להיות שלילי.';
    END IF;

    -- חישוב מושבים פנויים התחלתיים
    v_available_seats := r_vehicle.capacity - p_expected_passengers;

    -- הכנסת הנסיעה החדשה לטבלה
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
-- 3. הרצת הבדיקה (בתוך טרנזקציה שמבוטלת בסוף)
-- ==========================================
BEGIN;

-- הצגת הדשבורד במצב הנוכחי (לפני השינויים)
SELECT '=== 1. דשבורד מסלולים לפני הוספת הנסיעה ===' AS test_stage;
SELECT get_route_dashboard();
FETCH ALL FROM "route_dashboard_cursor";
CLOSE "route_dashboard_cursor";

-- בחירה דינמית של מזהים קיימים לטובת זימון הנסיעה
DO $$
DECLARE
    v_route_id INT;
    v_plate VARCHAR(20);
    v_driver_id INT;
    v_new_trip_id INT := 99999;
BEGIN
    SELECT route_id INTO v_route_id FROM route LIMIT 1;
    SELECT plate_number INTO v_plate FROM vehicle LIMIT 1;
    SELECT driver_id INTO v_driver_id FROM driver LIMIT 1;

    IF v_route_id IS NULL OR v_plate IS NULL OR v_driver_id IS NULL THEN
        RAISE EXCEPTION 'שגיאה: חסרים נתוני בסיס (מסלול, רכב או נהג) בטבלאות לצורך הבדיקה.';
    END IF;

    -- זימון נסיעה חדשה בתאריך עתידי (כולל היטלים מפורשים של טיפוסים)
    CALL schedule_new_trip(
        v_new_trip_id::INT, 
        v_route_id::INT, 
        (CURRENT_DATE + 30)::DATE, 
        '18:30'::VARCHAR, 
        5::INT, 
        v_plate::VARCHAR, 
        v_driver_id::INT
    );
END;
$$;

-- הצגת פרטי הנסיעה החדשה שהתווספה
SELECT '=== 3. בדיקת רשומת הנסיעה החדשה בטבלת הנסיעות ===' AS test_stage;
SELECT trip_id, trip_date, departure_time, available_seats, route_id, plate_number, driver_id
FROM trip
WHERE trip_id = 99999;

-- הדפסת דשבורד מעודכן - נשים לב שכמות הנסיעות העתידיות של המסלול גדלה ב-1!
SELECT '=== 4. דשבורד מסלולים לאחר הוספת הנסיעה (שים לב לעמודת future_trip_count) ===' AS test_stage;
SELECT get_route_dashboard();
FETCH ALL FROM "route_dashboard_cursor";
CLOSE "route_dashboard_cursor";

-- ביטול השינויים (ROLLBACK) לשמירה על בסיס נתונים נקי
SELECT '=== 5. ביצוע ROLLBACK לביטול הנתונים הזמניים ===' AS test_stage;
ROLLBACK;
