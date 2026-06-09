-- ==========================================
-- תוכנית ראשית 2: main_driver_and_occupancy
-- תיאור: מדגימה שיבוץ נהגים אוטומטי (auto_assign_drivers_to_future_trips)
--        וחישוב תפוסת נסיעה (calculate_trip_occupancy).
--        התוכנית מדגימה גם את השפעת טריגר הרישום על מקומות פנויים ותפוסה.
--        התוכנית מריצה הכל בטרנזקציה אחת מבוקרת ומבצעת בסופה ROLLBACK.
-- ==========================================

BEGIN;

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

-- חישוב תפוסה לאחר רישום הנוסע (נצפה לראות עליה במספר הרשומים וירידה במקומות הפנויים)
SELECT * FROM calculate_trip_occupancy(88888);

-- 5. עדכון סטטוס הרישום ל-Cancelled (להפעלת טריגר AFTER UPDATE)
SELECT '=== 5. עדכון סטטוס הרשמה ל-Cancelled (טריגר UPDATE מופעל ומחזיר מושב) ===' AS test_stage;
UPDATE registration 
SET status = 'Cancelled' 
WHERE reg_id = 77777;

-- חישוב תפוסה לאחר ביטול הרישום (נצפה לראות חזרה למצב המקורי)
SELECT * FROM calculate_trip_occupancy(88888);

-- 6. ביטול השינויים ושמירה על בסיס הנתונים נקי
SELECT '=== 6. ביצוע ROLLBACK לביטול הנתונים הזמניים ===' AS test_stage;
ROLLBACK;
