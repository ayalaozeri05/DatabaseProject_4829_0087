-- ==========================================
-- פרוצדורה: auto_assign_drivers_to_future_trips
-- תיאור: משבצת נהגים באופן אוטומטי ובשיטת סבב (Round-Robin) לכל הנסיעות
--        העתידיות שטרם שויך להן נהג (שדות driver_id בעלי ערך NULL).
--        הפרוצדורה משתמשת בכורסור מפורש ובלולאת LOOP/FETCH.
-- ==========================================

-- מחיקת הפרוצדורה במידה והיא קיימת
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
        
        -- תנאי יציאה מהלולאה - כאשר סיימנו לעבור על כל הנסיעות
        EXIT WHEN NOT FOUND;
        
        -- קביעת מזהה הנהג לפי סבב מעגלי (Round-Robin)
        v_assigned_driver_id := v_driver_ids[v_index];
        
        -- שליפת שם הנהג ושם המסלול לצורך הדפסת ההודעה
        SELECT driver_fullname INTO v_driver_name FROM driver WHERE driver_id = v_assigned_driver_id;
        SELECT route_name INTO v_route_name FROM route WHERE route_id = r_trip.route_id;
        
        -- עדכון הנהג בנסיעה
        UPDATE trip 
        SET driver_id = v_assigned_driver_id 
        WHERE trip_id = r_trip.trip_id;
        
        RAISE NOTICE 'שיבוץ אוטומטי: הנהג % (מזהה %) שובץ בהצלחה לנסיעה % בתאריך % (מסלול: %).', 
            v_driver_name, v_assigned_driver_id, r_trip.trip_id, r_trip.trip_date, v_route_name;
            
        -- קידום האינדקס הנהג במערך לצורך הסיבוב הבא
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
-- הרצת בדיקה לדוגמה (בתוך טרנזקציה שמבוטלת בסוף)
-- ==========================================
BEGIN;
DO $$
DECLARE
    v_route_id INT;
    v_plate VARCHAR(20);
BEGIN
    -- שליפת מזהים לדוגמה
    SELECT route_id INTO v_route_id FROM route LIMIT 1;
    SELECT plate_number INTO v_plate FROM vehicle LIMIT 1;

    -- הכנסת נסיעה עתידית לבדיקה (ללא נהג)
    IF v_route_id IS NOT NULL AND v_plate IS NOT NULL THEN
        INSERT INTO trip (trip_id, trip_date, departure_time, available_seats, route_id, plate_number, driver_id)
        VALUES (99977, CURRENT_DATE + 15, '12:00', 12, v_route_id, v_plate, NULL);
        
        RAISE NOTICE 'הוכנסה נסיעה עתידית זמנית 99977 ללא נהג.';
    END IF;
END;
$$;

-- הרצת תוכנית השיבוץ
CALL auto_assign_drivers_to_future_trips();

-- בדיקה האם הנסיעה קיבלה נהג
SELECT trip_id, trip_date, driver_id FROM trip WHERE trip_id = 99977;

-- ביטול השינויים
ROLLBACK;
