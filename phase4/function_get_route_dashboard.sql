-- ==========================================
-- פונקציה: get_route_dashboard
-- תיאור: מחזירה Ref Cursor המצביע לתוצאות ה-Dashboard של המסלולים במערכת.
--        הנתונים כוללים: מזהה מסלול, שם מסלול, שם אזור, מרחק כולל,
--        משך זמן מוערך, מספר תחנות במסלול ומספר נסיעות עתידיות.
-- ==========================================

-- מחיקת הפונקציה במידה והיא קיימת
DROP FUNCTION IF EXISTS get_route_dashboard();

CREATE OR REPLACE FUNCTION get_route_dashboard()
RETURNS refcursor AS $$
DECLARE
    r_cursor refcursor := 'route_dashboard_cursor';
    route_exists BOOLEAN;
BEGIN
    -- בדיקה האם קיימים מסלולים כלשהם במערכת (טיפול במצב שאין נתונים)
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
            -- חישוב כמות התחנות לכל מסלול מטבלת הקשר
            SELECT route_id, COUNT(stop_id) AS stop_count
            FROM route_stop
            GROUP BY route_id
        ) rs ON r.route_id = rs.route_id
        LEFT JOIN (
            -- חישוב כמות הנסיעות העתידיות (מהיום והלאה) לכל מסלול
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
-- הרצת בדיקה לדוגמה (בתוך טרנזקציה)
-- ==========================================
BEGIN;
-- הפעלת הפונקציה לקבלת ה-Cursor
SELECT get_route_dashboard();
-- שליפת כל הרשומות מתוך ה-Cursor שקיבלנו
FETCH ALL FROM "route_dashboard_cursor";
COMMIT;
