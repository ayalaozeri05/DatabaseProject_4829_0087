from db_connection import get_connection

conn = get_connection()
cur = conn.cursor()

# Update calculate_trip_occupancy
cur.execute("""
CREATE OR REPLACE FUNCTION public.calculate_trip_occupancy(p_trip_id integer)
 RETURNS TABLE(trip_id integer, capacity integer, available_seats integer, registered_passengers integer, occupancy_percent numeric, status_text character varying)
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_capacity INT;
    v_available_seats INT;
    v_registered_count INT;
    v_occupancy_pct NUMERIC;
    v_status VARCHAR(20);
    v_trip_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM trip WHERE trip.trip_id = p_trip_id) INTO v_trip_exists;
    IF NOT v_trip_exists THEN
        RAISE EXCEPTION 'Trip % not found.', p_trip_id;
    END IF;

    SELECT v.capacity, t.available_seats
    INTO v_capacity, v_available_seats
    FROM trip t
    JOIN vehicle v ON t.plate_number = v.plate_number
    WHERE t.trip_id = p_trip_id;

    -- Fix for mismatch when vehicle is changed
    IF v_available_seats > v_capacity THEN
        v_available_seats := v_capacity;
    END IF;

    SELECT COUNT(*)::INT
    INTO v_registered_count
    FROM registration r
    WHERE r.trip_id = p_trip_id
      AND (r.status IS NULL OR r.status <> 'Cancelled');

    IF v_capacity > 0 THEN
        v_occupancy_pct := ROUND(((v_capacity - v_available_seats)::NUMERIC / v_capacity::NUMERIC) * 100, 2);
    ELSE
        v_occupancy_pct := 0.00;
    END IF;

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
$function$;
""")

# Fix corrupted available_seats
cur.execute("""
UPDATE trip 
SET available_seats = v.capacity 
FROM vehicle v 
WHERE trip.plate_number = v.plate_number AND trip.available_seats > v.capacity;
""")

conn.commit()
print("Fixed calculation and corrupted data.")
