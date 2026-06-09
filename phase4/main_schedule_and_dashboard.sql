-- ==========================================
-- תוכנית ראשית 1: main_schedule_and_dashboard
-- תיאור: מדגימה זימון נסיעה חדשה (schedule_new_trip)
--        והצגת נתוני דשבורד מסלולים (get_route_dashboard).
--        התוכנית מריצה הכל בטרנזקציה אחת מבוקרת ומבצעת בסופה ROLLBACK.
-- ==========================================

BEGIN;

-- 1. הצגת הדשבורד במצב הנוכחי (לפני השינויים)
SELECT '=== 1. דשבורד מסלולים לפני הוספת הנסיעה ===' AS test_stage;
SELECT get_route_dashboard();
FETCH ALL FROM "route_dashboard_cursor";

-- 2. בחירה דינמית של מזהים קיימים לטובת זימון הנסיעה
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

    -- זימון נסיעה חדשה בתאריך עתידי עם 5 נוסעים צפויים
    CALL schedule_new_trip(
        v_new_trip_id, 
        v_route_id, 
        CURRENT_DATE + 30, 
        '18:30', 
        5, 
        v_plate, 
        v_driver_id
    );
END;
$$;

-- 3. הצגת פרטי הנסיעה החדשה שהתווספה
SELECT '=== 3. בדיקת רשומת הנסיעה החדשה בטבלת הנסיעות ===' AS test_stage;
SELECT trip_id, trip_date, departure_time, available_seats, route_id, plate_number, driver_id
FROM trip
WHERE trip_id = 99999;

-- 4. הדפסת דשבורד מעודכן - נשים לב שכמות הנסיעות העתידיות של המסלול גדלה ב-1!
SELECT '=== 4. דשבורד מסלולים לאחר הוספת הנסיעה (שים לב לעמודת future_trip_count) ===' AS test_stage;
SELECT get_route_dashboard();
FETCH ALL FROM "route_dashboard_cursor";

-- 5. ביטול השינויים (ROLLBACK) לשמירה על בסיס נתונים נקי
SELECT '=== 5. ביצוע ROLLBACK לביטול הנתונים הזמניים ===' AS test_stage;
ROLLBACK;
