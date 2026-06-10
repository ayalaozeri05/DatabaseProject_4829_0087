-- ==========================================
-- תוכנית ראשית 2: main_driver_and_occupancy
-- תיאור: יוצרת את הפרוצדורה והפונקציה הנדרשות בבסיס הנתונים (מחוץ לטרנזקציה)
--        ולאחר מכן מדגימה שיבוץ נהגים אוטומטי, חישוב תפוסה ופעילות טריגרים.
--        התוכנית מריצה את הבדיקה בתוך טרנזקציה ומבצעת בסופה ROLLBACK.
-- ==========================================

-- ==========================================
-- 1. יצירת הפרוצדורה auto_assign_drivers_to_future_trips
-- ==========================================
DROP PROCEDURE IF EXISTS auto_assign_drivers_to_future_trips();

CREATE OR REPLACE PROCEDURE auto_assign_drivers_to_future_trips()
AS $$
DECLARE
    -- כורסור מפורש לשליפת נסיעות עתידיות שבהן חסר נהג
    cur_trips CURSOR FOR 
        SELECT trip_id, trip_date, route_id 
        FROM trip 
        WHERE trip_date >= CURRENT_DATE AND driver_id IS NULL
        ORDER BY trip_date, trip_id;
        
    r_trip RECORD;
    v_driver_ids INT[];
    v_driver_count INT;
    v_index INT := 1;
    v_assigned_driver_id INT;
    v_driver_name VARCHAR(100);
    v_route_name VARCHAR(100);
BEGIN
    -- שליפת כל מזהי הנהגים הקיימים במערכת ומיונם לתוך מערך
    SELECT ARRAY(SELECT driver_id FROM driver ORDER BY driver_id) INTO v_driver_ids;
    v_driver_count := ARRAY_LENGTH(v_driver_ids, 1);
    
    -- אם אין נהגים במערכת, נמנע משיבוץ
    IF v_driver_count IS NULL OR v_driver_count = 0 THEN
        RAISE EXCEPTION 'שגיאה: לא נמצאו נהגים במערכת לצורך שיבוץ אוטומטי.';
    END IF;

    -- פתיחת הכורסור
    OPEN cur_trips;
    
    LOOP
        -- שליפת השורה הבאה לתוך ה-RECORD
        FETCH cur_trips INTO r_trip;
        
        -- תנאי יציאה מהלולאה
        EXIT WHEN NOT FOUND;
        
        -- קביעת מזהה הנהג לפי סבב מעגלי (Round-Robin)
        v_assigned_driver_id := v_driver_ids[v_index];
        
        -- שליפת שם הנהג ושם המסלול
        SELECT driver_fullname INTO v_driver_name FROM driver WHERE driver_id = v_assigned_driver_id;
        SELECT route_name INTO v_route_name FROM route WHERE route_id = r_trip.route_id;
        
        -- עדכון הנהג בנסיעה
        UPDATE trip 
        SET driver_id = v_assigned_driver_id 
        WHERE trip_id = r_trip.trip_id;
        
        RAISE NOTICE 'שיבוץ אוטומטי: הנהג % (מזהה %) שובץ בהצלחה לנסיעה % בתאריך % (מסלול: %).', 
            v_driver_name, v_assigned_driver_id, r_trip.trip_id, r_trip.trip_date, v_route_name;
            
        -- קידום האינדקס הנהג במערך
        v_index := v_index + 1;
        IF v_index > v_driver_count THEN
            v_index := 1;
        END IF;
    END LOOP;
    
    -- סגירת הכורסור
    CLOSE cur_trips;
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'שגיאה במהלך שיבוץ הנהגים האוטומטי: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;


-- ==========================================
-- 2. יצירת הפונקציה calculate_trip_occupancy
-- ==========================================
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
    -- בדיקה האם הנסיעה קיימת
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

    -- ספירת הנוסעים הרשומים
    SELECT COUNT(*)::INT
    INTO v_registered_count
    FROM registration r
    WHERE r.trip_id = p_trip_id
      AND (r.status IS NULL OR r.status <> 'Cancelled');

    -- חישוב אחוז התפוסה
    IF v_capacity > 0 THEN
        v_occupancy_pct := ROUND((v_registered_count::NUMERIC / v_capacity::NUMERIC) * 100, 2);
    ELSE
        v_occupancy_pct := 0.00;
    END IF;

    -- קביעת הסטטוס המילולי
    IF v_occupancy_pct >= 100.00 OR v_available_seats = 0 THEN
        v_status := 'FULL';
    ELSIF v_occupancy_pct >= 80.00 THEN
        v_status := 'ALMOST FULL';
    ELSE
        v_status := 'AVAILABLE';
    END IF;

    RETURN QUERY
    SELECT p_trip_id, v_capacity, v_available_seats, v_registered_count, v_occupancy_pct, v_status;
END;
$$ LANGUAGE plpgsql;


-- ==========================================
-- 3. הרצת הבדיקה (בתוך טרנזקציה שמבוטלת בסוף)
-- ==========================================
BEGIN;

-- מחיקה מקדימה של נתוני בדיקה קודמים כדי למנוע התנגשויות (אם קיימים בטבלאות)
DELETE FROM registration WHERE reg_id = 77777;
DELETE FROM trip WHERE trip_id = 88888;

-- 1. הכנסת נסיעה עתידית זמנית ללא נהג (driver_id IS NULL)
SELECT '=== 1. יצירת נסיעה עתידית ללא נהג לצורך בדיקת שיבוץ אוטומטי ===' AS test_stage;

DO $$
DECLARE
    v_route_id INT;
    v_plate VARCHAR(20);
BEGIN
    SELECT route_id INTO v_route_id FROM route LIMIT 1;
    SELECT plate_number INTO v_plate FROM vehicle LIMIT 1;

    IF v_route_id IS NULL OR v_plate IS NULL THEN
        RAISE EXCEPTION 'שגיאה: חסרים נתוני בסיס (מסלול או רכב) בטבלאות לצורך הבדיקה.';
    END IF;

    -- יצירת נסיעה עם מזהה זמני 88888 ללא נהג
    INSERT INTO trip (trip_id, trip_date, departure_time, available_seats, route_id, plate_number, driver_id)
    VALUES (88888, CURRENT_DATE + 10, '14:00', 10, v_route_id, v_plate, NULL);
END;
$$;

-- בדיקה שהנסיעה אכן קיימת ושדה נהג ריק
SELECT trip_id, trip_date, driver_id AS assigned_driver
FROM trip 
WHERE trip_id = 88888;

-- 2. הפעלת שיבוץ נהגים אוטומטי בסבב
SELECT '=== 2. הפעלת הפרוצדורה לשיבוץ נהגים אוטומטי ===' AS test_stage;
CALL auto_assign_drivers_to_future_trips();

-- הצגת רשומת הנסיעה לאחר השיבוץ (לוודא שנוסף נהג)
SELECT trip_id, trip_date, driver_id AS assigned_driver
FROM trip 
WHERE trip_id = 88888;

-- 3. חישוב תפוסה לפני רישום נוסעים
SELECT '=== 3. חישוב תפוסת נסיעה 88888 לפני הרשמה ===' AS test_stage;
SELECT * FROM calculate_trip_occupancy(88888);

-- 4. רישום נוסע לנסיעה (להפעלת טריגר AFTER INSERT)
SELECT '=== 4. ביצוע רישום נוסע לנסיעה 88888 (טריגר INSERT מופעל) ===' AS test_stage;
DO $$
DECLARE
    v_pass_id INT;
    v_stop_id INT;
BEGIN
    SELECT pass_id INTO v_pass_id FROM passenger LIMIT 1;
    SELECT stop_id INTO v_stop_id FROM stop LIMIT 1;

    IF v_pass_id IS NULL OR v_stop_id IS NULL THEN
        RAISE EXCEPTION 'שגיאה: חסרים נתוני בסיס (נוסע או תחנה) בטבלאות לצורך הבדיקה.';
    END IF;

    -- הכנסת רישום חדש מזהה זמני 77777 בסטטוס Confirmed
    INSERT INTO registration (reg_id, status, pass_id, trip_id, boarding_stop_id, dropoff_stop_id)
    VALUES (77777, 'Confirmed', v_pass_id, 88888, v_stop_id, v_stop_id);
END;
$$;

-- חישוב תפוסה לאחר רישום הנוסע
SELECT * FROM calculate_trip_occupancy(88888);

-- 5. עדכון סטטוס הרישום ל-Cancelled (להפעלת טריגר AFTER UPDATE)
SELECT '=== 5. עדכון סטטוס הרשמה ל-Cancelled (טריגר UPDATE מופעל ומחזיר מושב) ===' AS test_stage;
UPDATE registration 
SET status = 'Cancelled' 
WHERE reg_id = 77777;

-- חישוב תפוסה לאחר ביטול הרישום
SELECT * FROM calculate_trip_occupancy(88888);

-- 6. ביטול השינויים ושמירה על בסיס הנתונים נקי
SELECT '=== 6. ביצוע ROLLBACK לביטול הנתונים הזמניים ===' AS test_stage;
ROLLBACK;
