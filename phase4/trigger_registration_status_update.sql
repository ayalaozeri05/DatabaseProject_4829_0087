    -- ==========================================
    -- טריגר: registration_status_update
    -- תיאור: מופעל לאחר עדכון בטבלת registration.
    --        אם הסטטוס משתנה מ'Cancelled' לסטטוס פעיל, יירד מקום פנוי בנסיעה (במידה ויש מקום).
    --        אם הסטטוס משתנה מסטטוס פעיל ל'Cancelled', יוחזר מקום פנוי בנסיעה (עד לקיבולת הרכב).
    -- ==========================================

    -- מחיקת הטריגר והפונקציה במידה והם קיימים
    DROP TRIGGER IF EXISTS registration_status_update_trigger ON registration;
    DROP FUNCTION IF EXISTS trg_registration_status_update();

    CREATE OR REPLACE FUNCTION trg_registration_status_update()
    RETURNS TRIGGER AS $$
    DECLARE
        v_seats INT;
        v_capacity INT;
    BEGIN
        -- נבצע את הלוגיקה רק אם חל שינוי אמיתי בעמודת הסטטוס
        IF OLD.status IS DISTINCT FROM NEW.status THEN
            
            -- 1. שינוי סטטוס מ-Cancelled לסטטוס פעיל (למשל Confirmed או Completed)
            IF (OLD.status = 'Cancelled' OR OLD.status IS NULL) AND NEW.status <> 'Cancelled' THEN
                -- נעילת שורת הנסיעה
                SELECT available_seats INTO v_seats
                FROM trip
                WHERE trip_id = NEW.trip_id
                FOR UPDATE;
                
                -- בדיקה האם יש מקום פנוי
                IF v_seats <= 0 THEN
                    RAISE EXCEPTION 'שגיאה: לא ניתן להפעיל מחדש את הרישום מספר %: אין מקומות פנויים בנסיעה %!', NEW.reg_id, NEW.trip_id;
                END IF;
                
                -- הורדת מקום פנוי
                UPDATE trip
                SET available_seats = available_seats - 1
                WHERE trip_id = NEW.trip_id;
                
                RAISE NOTICE 'עדכון הרשמה: סטטוס ההרשמה % שונה לפעיל. ירד מושב בנסיעה % (נותרו % מקומות פנויים).',
                    NEW.reg_id, NEW.trip_id, v_seats - 1;
                    
            -- 2. שינוי סטטוס מסטטוס פעיל ל-Cancelled
            ELSIF (OLD.status <> 'Cancelled' OR OLD.status IS NULL) AND NEW.status = 'Cancelled' THEN
                -- נעילת שורת הנסיעה ושליפת הקיבולת של הרכב המשויך
                SELECT t.available_seats, v.capacity 
                INTO v_seats, v_capacity
                FROM trip t
                JOIN vehicle v ON t.plate_number = v.plate_number
                WHERE t.trip_id = NEW.trip_id
                FOR UPDATE;
                
                -- מניעת חריגה מעבר לקיבולת המקסימלית של הרכב
                IF v_seats < v_capacity THEN
                    UPDATE trip
                    SET available_seats = available_seats + 1
                    WHERE trip_id = NEW.trip_id;
                    
                    RAISE NOTICE 'עדכון הרשמה: ההרשמה % בוטלה. הוחזר מושב לנסיעה % (יש כעת % מקומות פנויים מתוך קיבולת של %).',
                        NEW.reg_id, NEW.trip_id, v_seats + 1, v_capacity;
                ELSE
                    RAISE NOTICE 'הערה: מספר המושבים הפנויים בנסיעה % כבר שווה לקיבולת המקסימלית (%). לא בוצע עדכון נוסף.',
                        NEW.trip_id, v_capacity;
                END IF;
            END IF;
            
        END IF;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- יצירת הטריגר
    CREATE TRIGGER registration_status_update_trigger
    AFTER UPDATE ON registration
    FOR EACH ROW
    EXECUTE FUNCTION trg_registration_status_update();

    -- ==========================================
    -- הרצת בדיקה לדוגמה (ללא טרנזקציה על מנת לשמור על הטריגר בבסיס הנתונים)
    -- ==========================================
    -- ניקוי מקדים של מפתח הבדיקה כדי למנוע שגיאות הרצה חוזרת
    DELETE FROM registration WHERE reg_id = 99902;

    DO $$
    DECLARE
        v_trip_id INT;
        v_pass_id INT;
        v_stop_id INT;
    BEGIN
        -- שליפת מזהים קיימים מהטבלאות
        SELECT trip_id INTO v_trip_id FROM trip WHERE available_seats > 1 LIMIT 1;
        SELECT pass_id INTO v_pass_id FROM passenger LIMIT 1;
        SELECT stop_id INTO v_stop_id FROM stop LIMIT 1;

        IF v_trip_id IS NOT NULL AND v_pass_id IS NOT NULL AND v_stop_id IS NOT NULL THEN
            -- 1. הכנסת הרשמה מבוטלת (לא משפיעה על המקומות)
            INSERT INTO registration (reg_id, status, pass_id, trip_id, boarding_stop_id, dropoff_stop_id)
            VALUES (99902, 'Cancelled', v_pass_id, v_trip_id, v_stop_id, v_stop_id);
            
            RAISE NOTICE 'מושבים פנויים לפני הפעלת הרשמה: %', 
                (SELECT available_seats FROM trip WHERE trip_id = v_trip_id);
                
            -- 2. עדכון סטטוס לפעיל (מפעיל את טריגר ה-UPDATE ומוריד מקום פנוי)
            UPDATE registration SET status = 'Confirmed' WHERE reg_id = 99902;
            
            RAISE NOTICE 'מושבים פנויים לאחר הפעלת הרשמה: %', 
                (SELECT available_seats FROM trip WHERE trip_id = v_trip_id);
                
            -- 3. ביטול הרשמה מחדש (מחזיר מקום פנוי)
            UPDATE registration SET status = 'Cancelled' WHERE reg_id = 99902;
            
            RAISE NOTICE 'מושבים פנויים לאחר ביטול חוזר של הרשמה: %', 
                (SELECT available_seats FROM trip WHERE trip_id = v_trip_id);
        END IF;
    END;
    $$;

    -- ניקוי נתוני הבדיקה בלבד (משאיר את הטריגר קיים בבסיס הנתונים)
    -- הערה: מכיוון שההרשמה מבוטלת כעת (Cancelled), מספר המקומות הפנויים חזר לקדמותו.
    -- מחיקת הרשומה לא תפעיל מחדש את הטריגר כי היא מבוטלת (או שהטריגר מופעל רק על INSERT/UPDATE).
    DELETE FROM registration WHERE reg_id = 99902;

