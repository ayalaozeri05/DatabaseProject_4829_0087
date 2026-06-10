-- ==========================================
-- טריגר: registration_after_insert
-- תיאור: מופעל לאחר הכנסת רישום חדש לטבלת registration.
--        אם הסטטוס אינו 'Cancelled', הטריגר יפחית מושב פנוי אחד
--        בטבלת trip עבור הנסיעה המתאימה.
--        אם אין מושבים פנויים, תיזרק שגיאה וההרשמה תבוטל.
-- ==========================================

-- מחיקת הטריגר והפונקציה במידה והם קיימים
DROP TRIGGER IF EXISTS registration_after_insert_trigger ON registration;
DROP FUNCTION IF EXISTS trg_registration_after_insert();

CREATE OR REPLACE FUNCTION trg_registration_after_insert()
RETURNS TRIGGER AS $$
DECLARE
    v_seats INT;
BEGIN
    -- נבצע עדכון מושבים רק אם הרישום החדש אינו בסטטוס מבוטל
    IF NEW.status IS DISTINCT FROM 'Cancelled' THEN
        -- נעילת שורת הנסיעה למניעת בעיות Race Condition (שימוש ב-FOR UPDATE)
        SELECT available_seats INTO v_seats
        FROM trip
        WHERE trip_id = NEW.trip_id
        FOR UPDATE;
        
        -- בדיקה האם הנסיעה קיימת
        IF v_seats IS NULL THEN
            RAISE EXCEPTION 'שגיאה: נסיעה מספר % אינה קיימת במערכת.', NEW.trip_id;
        -- בדיקה האם יש מקומות פנויים
        ELSIF v_seats <= 0 THEN
            RAISE EXCEPTION 'שגיאה: לא ניתן להירשם לנסיעה %: אין מקומות פנויים (Available Seats = 0)!', NEW.trip_id;
        END IF;

        -- עדכון מספר המקומות הפנויים בנסיעה (הורדה ב-1)
        UPDATE trip
        SET available_seats = available_seats - 1
        WHERE trip_id = NEW.trip_id;
        
        RAISE NOTICE 'ההרשמה % התקבלה בהצלחה. עודכן מושב פנוי בנסיעה % (נותרו % מקומות פנויים).', 
            NEW.reg_id, NEW.trip_id, v_seats - 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- יצירת הטריגר
CREATE TRIGGER registration_after_insert_trigger
AFTER INSERT ON registration
FOR EACH ROW
EXECUTE FUNCTION trg_registration_after_insert();

-- ==========================================
-- הרצת בדיקה לדוגמה (ללא טרנזקציה על מנת לשמור על הטריגר בבסיס הנתונים)
-- ==========================================
-- ניקוי מקדים של מפתח הבדיקה כדי למנוע שגיאות הרצה חוזרת
DELETE FROM registration WHERE reg_id = 99901;

DO $$
DECLARE
    v_trip_id INT;
    v_pass_id INT;
    v_stop_id INT;
BEGIN
    -- שליפת מזהים קיימים
    SELECT trip_id INTO v_trip_id FROM trip WHERE available_seats > 0 LIMIT 1;
    SELECT pass_id INTO v_pass_id FROM passenger LIMIT 1;
    SELECT stop_id INTO v_stop_id FROM stop LIMIT 1;

    -- הצגת מקומות פנויים לפני ההרשמה
    IF v_trip_id IS NOT NULL THEN
        RAISE NOTICE 'מקומות פנויים לפני הרשמה בנסיעה %: %', 
            v_trip_id, (SELECT available_seats FROM trip WHERE trip_id = v_trip_id);
    END IF;

    -- הכנסת רישום חדש (מפעיל את הטריגר)
    IF v_trip_id IS NOT NULL AND v_pass_id IS NOT NULL AND v_stop_id IS NOT NULL THEN
        INSERT INTO registration (reg_id, status, pass_id, trip_id, boarding_stop_id, dropoff_stop_id)
        VALUES (99901, 'Confirmed', v_pass_id, v_trip_id, v_stop_id, v_stop_id);
    END IF;
END;
$$;

-- בדיקה שמספר המקומות הפנויים התעדכן
SELECT trip_id, available_seats FROM trip WHERE trip_id = (SELECT trip_id FROM registration WHERE reg_id = 99901);

-- החזרת המצב לקדמותו וניקוי נתוני הבדיקה בלבד (משאיר את הטריגר קיים בבסיס הנתונים)
UPDATE trip 
SET available_seats = available_seats + 1 
WHERE trip_id = (SELECT trip_id FROM registration WHERE reg_id = 99901);

DELETE FROM registration WHERE reg_id = 99901;

