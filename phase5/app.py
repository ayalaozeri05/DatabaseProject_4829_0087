"""
app.py – TransRoute Planner Web App (Flask)
Run: py app.py  → open http://localhost:5000
"""
from flask import Flask, jsonify, request, render_template, abort
from werkzeug.exceptions import HTTPException
import psycopg2.errors
from db_connection import (fetch_all, fetch_one, execute_dml,
                           call_procedure, call_refcursor_function,
                           call_table_function)
from datetime import date

app = Flask(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify(error=str(e.description)), e.code
    if isinstance(e, psycopg2.errors.IntegrityError):
        return jsonify(error="Operation failed due to related records constraint. Cannot delete or update because it is in use by another table."), 400
    if isinstance(e, psycopg2.Error):
        return jsonify(error=f"Database error: {e.pgerror or str(e)}"), 400
    return jsonify(error="Internal server error: " + str(e)), 500


# ─── Helper ───────────────────────────────────────────────────────────────────
def auto_id(table, col):
    r = fetch_one(f"SELECT COALESCE(MAX({col}),0)+1 AS n FROM {table}")
    return r["n"] if r else 1

def ok(msg="OK", **kw):
    return jsonify({"message": msg, **kw})

# ─── Page views ───────────────────────────────────────────────────────────────
@app.route("/")
def pg_dashboard(): return render_template("dashboard.html")
@app.route("/routes")
def pg_routes(): return render_template("routes.html")
@app.route("/trips")
def pg_trips(): return render_template("trips.html")
@app.route("/vehicles")
def pg_vehicles(): return render_template("vehicles.html")
@app.route("/drivers")
def pg_drivers(): return render_template("drivers.html")
@app.route("/passengers")
def pg_passengers(): return render_template("passengers.html")
@app.route("/stops")
def pg_stops(): return render_template("stops.html")
@app.route("/queries")
def pg_queries(): return render_template("queries.html")

# ─── Dashboard stats ──────────────────────────────────────────────────────────
@app.route("/api/stats")
def api_stats():
    def cnt(q): 
        try: return fetch_one(q)["n"]
        except: return 0
    return jsonify({
        "routes":      cnt("SELECT COUNT(*) AS n FROM route"),
        "trips":       cnt("SELECT COUNT(*) AS n FROM trip"),
        "vehicles":    cnt("SELECT COUNT(*) AS n FROM vehicle"),
        "drivers":     cnt("SELECT COUNT(*) AS n FROM driver"),
        "passengers":  cnt("SELECT COUNT(*) AS n FROM passenger"),
        "stops":       cnt("SELECT COUNT(*) AS n FROM stop"),
        "today":       cnt("SELECT COUNT(*) AS n FROM trip WHERE trip_date=CURRENT_DATE"),
        "future":      cnt("SELECT COUNT(*) AS n FROM trip WHERE trip_date>CURRENT_DATE"),
        "no_driver":   cnt("SELECT COUNT(*) AS n FROM trip WHERE trip_date>=CURRENT_DATE AND driver_id IS NULL"),
    })

@app.route("/api/stats/recent_trips")
def api_recent_trips():
    rows = fetch_all("""
        SELECT t.trip_id, t.trip_date, t.departure_time, r.route_name,
               COALESCE(d.driver_fullname,'—') AS driver_name,
               t.available_seats,
               ROUND(((v.capacity-t.available_seats)::numeric/NULLIF(v.capacity,0))*100,1) AS pct
        FROM trip t
        JOIN route r ON r.route_id=t.route_id
        JOIN vehicle v ON v.plate_number=t.plate_number
        LEFT JOIN driver d ON d.driver_id=t.driver_id
        ORDER BY t.trip_date DESC, t.departure_time DESC LIMIT 20
    """)
    return jsonify(rows)

# ─── Lookup endpoints (for dropdowns) ─────────────────────────────────────────
@app.route("/api/lookup/regions")
def lk_regions():
    return jsonify(fetch_all("SELECT region_id, regio_name FROM region ORDER BY regio_name"))

@app.route("/api/lookup/routes")
def lk_routes():
    return jsonify(fetch_all("SELECT route_id, route_name FROM route ORDER BY route_name"))

@app.route("/api/lookup/vehicles")
def lk_vehicles():
    return jsonify(fetch_all("SELECT plate_number, vehicle_type, capacity FROM vehicle ORDER BY plate_number"))

@app.route("/api/lookup/drivers")
def lk_drivers():
    return jsonify(fetch_all("SELECT driver_id, driver_fullname FROM driver ORDER BY driver_fullname"))

@app.route("/api/lookup/trips")
def lk_trips():
    return jsonify(fetch_all("""
        SELECT t.trip_id, t.trip_date::text||' '||t.departure_time AS label, r.route_name
        FROM trip t JOIN route r ON r.route_id=t.route_id
        ORDER BY t.trip_date DESC, t.departure_time
    """))

@app.route("/api/lookup/stops")
def lk_stops():
    return jsonify(fetch_all("SELECT stop_id, stop_name FROM stop ORDER BY stop_name"))

@app.route("/api/lookup/sites")
def lk_sites():
    return jsonify(fetch_all("SELECT site_name FROM site ORDER BY site_name"))

# ─── ROUTES CRUD ──────────────────────────────────────────────────────────────
@app.route("/api/routes", methods=["GET"])
def api_routes_list():
    return jsonify(fetch_all("""
        SELECT r.route_id, r.route_name, reg.regio_name AS region,
               r.start_location, r.end_location,
               r.total_distance_km AS distance_km,
               r.estimated_duration_minutes AS duration_min,
               COALESCE(rs.sc,0)::int AS stops,
               COALESCE(t.ft,0)::int AS future_trips
        FROM route r
        LEFT JOIN region reg ON reg.region_id=r.region_id
        LEFT JOIN (SELECT route_id,COUNT(*) AS sc FROM route_stop GROUP BY route_id) rs ON rs.route_id=r.route_id
        LEFT JOIN (SELECT route_id,COUNT(*) AS ft FROM trip WHERE trip_date>=CURRENT_DATE GROUP BY route_id) t ON t.route_id=r.route_id
        ORDER BY r.route_id
    """))

@app.route("/api/routes/<int:rid>", methods=["GET"])
def api_routes_get(rid):
    r = fetch_one("SELECT * FROM route WHERE route_id=%s", (rid,))
    return jsonify(r) if r else abort(404)

@app.route("/api/routes", methods=["POST"])
def api_routes_create():
    d = request.json
    nid = auto_id("route","route_id")
    execute_dml("""INSERT INTO route(route_id,route_name,start_location,end_location,
        total_distance_km,estimated_duration_minutes,created_date,region_id)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
        (nid,d["route_name"],d["start_location"],d["end_location"],
         float(d["distance_km"]),int(d["duration_min"]),str(date.today()),int(d["region_id"])))
    
    # שילוב משלב 2: עדכון אוטומטי למסלולים ארוכים
    execute_dml("UPDATE route SET estimated_duration_minutes = estimated_duration_minutes + 15 WHERE total_distance_km > 150")
    
    return ok("Route created", id=nid), 201

@app.route("/api/routes/<int:rid>", methods=["PUT"])
def api_routes_update(rid):
    d = request.json
    execute_dml("""UPDATE route SET route_name=%s,start_location=%s,end_location=%s,
        total_distance_km=%s,estimated_duration_minutes=%s,region_id=%s WHERE route_id=%s""",
        (d["route_name"],d["start_location"],d["end_location"],
         float(d["distance_km"]),int(d["duration_min"]),int(d["region_id"]),rid))
    
    # שילוב משלב 2: עדכון אוטומטי למסלולים ארוכים
    execute_dml("UPDATE route SET estimated_duration_minutes = estimated_duration_minutes + 15 WHERE total_distance_km > 150")
    
    return ok("Route updated")

@app.route("/api/routes/<int:rid>", methods=["DELETE"])
def api_routes_delete(rid):
    execute_dml("DELETE FROM registration WHERE trip_id IN (SELECT trip_id FROM trip WHERE route_id=%s)",(rid,))
    execute_dml("DELETE FROM trip WHERE route_id=%s",(rid,))
    execute_dml("DELETE FROM route_stop WHERE route_id=%s",(rid,))
    execute_dml("DELETE FROM route WHERE route_id=%s",(rid,))
    return ok("Route deleted")

# ─── TRIPS CRUD ───────────────────────────────────────────────────────────────
@app.route("/api/trips", methods=["GET"])
def api_trips_list():
    # שילוב משלב 2: איפוס מקומות פנויים לנסיעות שעברו לפני טעינת הרשימה
    execute_dml("UPDATE trip SET available_seats = 0 WHERE trip_date < CURRENT_DATE AND available_seats > 0")
    
    # שילוב משלב 4: שיבוץ אוטומטי של נהגים פנויים לטיולים עתידיים בכל פעם שטוענים את רשימת הטיולים!
    try:
        call_procedure("auto_assign_drivers_to_future_trips", [])
    except Exception as e:
        print("Auto-assign failed:", e)
        
    return jsonify(fetch_all("""
        SELECT t.trip_id, t.trip_date, t.departure_time, r.route_name,
               COALESCE(d.driver_fullname,'—') AS driver_name,
               t.plate_number, v.capacity, t.available_seats,
               ROUND(((v.capacity-t.available_seats)::numeric/NULLIF(v.capacity,0))*100,1) AS occupancy_pct
        FROM trip t
        JOIN route r ON r.route_id=t.route_id
        JOIN vehicle v ON v.plate_number=t.plate_number
        LEFT JOIN driver d ON d.driver_id=t.driver_id
        ORDER BY t.trip_date DESC, t.departure_time DESC
    """))

@app.route("/api/trips/<int:tid>", methods=["GET"])
def api_trips_get(tid):
    r = fetch_one("SELECT * FROM trip WHERE trip_id=%s",(tid,))
    
    # שילוב משלב 4: שימוש בפונקציית הטבלה כדי להעשיר את פרטי הטיול בנתוני תפוסה!
    try:
        if r:
            occ = fetch_one("SELECT * FROM calculate_trip_occupancy(%s)", (tid,))
            if occ:
                r['occupancy_status'] = occ['status_text']
                r['occupancy_percent'] = occ['occupancy_percent']
    except Exception as e:
        print("Occupancy function failed:", e)
        
    return jsonify(r) if r else abort(404)

@app.route("/api/trips", methods=["POST"])
def api_trips_create():
    d = request.json
    nid = auto_id("trip","trip_id")
    did = int(d["driver_id"]) if d.get("driver_id") else None
    expected_passengers = int(d.get("booked", 0))
    
    try:
        # שימוש בפרוצדורה משלב 4 במקום INSERT רגיל!
        call_procedure("schedule_new_trip", (
            nid,
            int(d["route_id"]),
            d["trip_date"],
            str(d["departure_time"]),
            expected_passengers,
            str(d["plate_number"]),
            did
        ))
        return ok("Trip created using Stored Procedure", id=nid), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/trips/<int:tid>", methods=["PUT"])
def api_trips_update(tid):
    d = request.json
    did = int(d["driver_id"]) if d.get("driver_id") else None
    execute_dml("""UPDATE trip SET trip_date=%s,departure_time=%s,
        route_id=%s,plate_number=%s,driver_id=%s WHERE trip_id=%s""",
        (d["trip_date"],d["departure_time"],int(d["route_id"]),d["plate_number"],did,tid))
    return ok("Trip updated")

@app.route("/api/trips/<int:tid>", methods=["DELETE"])
def api_trips_delete(tid):
    execute_dml("DELETE FROM registration WHERE trip_id=%s",(tid,))
    execute_dml("DELETE FROM trip WHERE trip_id=%s",(tid,))
    return ok("Trip deleted")

# ─── VEHICLES CRUD ────────────────────────────────────────────────────────────
@app.route("/api/vehicles", methods=["GET"])
def api_vehicles_list():
    return jsonify(fetch_all("""
        SELECT v.plate_number, v.vehicle_type, v.capacity,
               COUNT(DISTINCT t.trip_id) AS total_trips,
               STRING_AGG(DISTINCT reg.regio_name,', ') AS regions
        FROM vehicle v
        LEFT JOIN trip t ON t.plate_number=v.plate_number
        LEFT JOIN region_vehicle rv ON rv.plate_number=v.plate_number
        LEFT JOIN region reg ON reg.region_id=rv.region_id
        GROUP BY v.plate_number,v.vehicle_type,v.capacity
        ORDER BY total_trips DESC
    """))

@app.route("/api/vehicles/<plate>", methods=["GET"])
def api_vehicles_get(plate):
    r = fetch_one("SELECT * FROM vehicle WHERE plate_number=%s",(plate,))
    return jsonify(r) if r else abort(404)

@app.route("/api/vehicles", methods=["POST"])
def api_vehicles_create():
    d = request.json
    execute_dml("INSERT INTO vehicle(plate_number,vehicle_type,capacity) VALUES(%s,%s,%s)",
                (d["plate_number"],d["vehicle_type"],int(d["capacity"])))
    return ok("Vehicle created"), 201

@app.route("/api/vehicles/<plate>", methods=["PUT"])
def api_vehicles_update(plate):
    d = request.json
    execute_dml("UPDATE vehicle SET vehicle_type=%s,capacity=%s WHERE plate_number=%s",
                (d["vehicle_type"],int(d["capacity"]),plate))
    return ok("Vehicle updated")

@app.route("/api/vehicles/<plate>", methods=["DELETE"])
def api_vehicles_delete(plate):
    execute_dml("DELETE FROM registration WHERE trip_id IN (SELECT trip_id FROM trip WHERE plate_number=%s)",(plate,))
    execute_dml("DELETE FROM trip WHERE plate_number=%s",(plate,))
    execute_dml("DELETE FROM region_vehicle WHERE plate_number=%s",(plate,))
    execute_dml("DELETE FROM vehicle WHERE plate_number=%s",(plate,))
    return ok("Vehicle deleted")

# ─── DRIVERS CRUD ─────────────────────────────────────────────────────────────
@app.route("/api/drivers", methods=["GET"])
def api_drivers_list():
    return jsonify(fetch_all("""
        SELECT d.driver_id, d.driver_fullname, d.licensetype,
               COUNT(t.trip_id) AS total_trips,
               COUNT(t.trip_id) FILTER (WHERE t.trip_date>=CURRENT_DATE) AS upcoming
        FROM driver d LEFT JOIN trip t ON t.driver_id=d.driver_id
        GROUP BY d.driver_id,d.driver_fullname,d.licensetype
        ORDER BY upcoming DESC, d.driver_fullname
    """))

@app.route("/api/drivers/<int:did>", methods=["GET"])
def api_drivers_get(did):
    r = fetch_one("SELECT * FROM driver WHERE driver_id=%s",(did,))
    return jsonify(r) if r else abort(404)

@app.route("/api/drivers", methods=["POST"])
def api_drivers_create():
    d = request.json
    nid = auto_id("driver","driver_id")
    execute_dml("INSERT INTO driver(driver_id,driver_fullname,licensetype) VALUES(%s,%s,%s)",
                (nid,d["driver_fullname"],d.get("licensetype") or None))
    return ok("Driver created", id=nid), 201

@app.route("/api/drivers/<int:did>", methods=["PUT"])
def api_drivers_update(did):
    d = request.json
    execute_dml("UPDATE driver SET driver_fullname=%s,licensetype=%s WHERE driver_id=%s",
                (d["driver_fullname"],d.get("licensetype") or None,did))
    return ok("Driver updated")

@app.route("/api/drivers/<int:did>", methods=["DELETE"])
def api_drivers_delete(did):
    execute_dml("UPDATE trip SET driver_id=NULL WHERE driver_id=%s",(did,))
    execute_dml("DELETE FROM driver WHERE driver_id=%s",(did,))
    return ok("Driver deleted")

# ─── PASSENGERS CRUD ──────────────────────────────────────────────────────────
@app.route("/api/passengers", methods=["GET"])
def api_passengers_list():
    return jsonify(fetch_all("""
        SELECT p.pass_id, p.pass_fullname, p.phone, COUNT(r.reg_id) AS registrations
        FROM passenger p LEFT JOIN registration r ON r.pass_id=p.pass_id
        GROUP BY p.pass_id,p.pass_fullname,p.phone ORDER BY p.pass_fullname
    """))

@app.route("/api/passengers/<int:pid>", methods=["GET"])
def api_passengers_get(pid):
    r = fetch_one("SELECT * FROM passenger WHERE pass_id=%s",(pid,))
    return jsonify(r) if r else abort(404)

@app.route("/api/passengers", methods=["POST"])
def api_passengers_create():
    d = request.json
    nid = auto_id("passenger","pass_id")
    execute_dml("INSERT INTO passenger(pass_id,pass_fullname,phone) VALUES(%s,%s,%s)",
                (nid,d["pass_fullname"],d.get("phone") or None))
    return ok("Passenger created", id=nid), 201

@app.route("/api/passengers/<int:pid>", methods=["PUT"])
def api_passengers_update(pid):
    d = request.json
    execute_dml("UPDATE passenger SET pass_fullname=%s,phone=%s WHERE pass_id=%s",
                (d["pass_fullname"],d.get("phone") or None,pid))
    return ok("Passenger updated")

@app.route("/api/passengers/<int:pid>", methods=["DELETE"])
def api_passengers_delete(pid):
    execute_dml("DELETE FROM registration WHERE pass_id=%s",(pid,))
    execute_dml("DELETE FROM passenger WHERE pass_id=%s",(pid,))
    return ok("Passenger deleted")

# ─── REGISTRATIONS CRUD ───────────────────────────────────────────────────────
@app.route("/api/registrations")
def api_regs_list():
    pid = request.args.get("pass_id")
    where = f"WHERE reg.pass_id={int(pid)}" if pid else ""
    return jsonify(fetch_all(f"""
        SELECT reg.reg_id, p.pass_fullname, t.trip_date, t.departure_time,
               r.route_name, COALESCE(sb.stop_name,'—') AS boarding,
               COALESCE(sd.stop_name,'—') AS dropoff,
               COALESCE(reg.status,'—') AS status, reg.pass_id, reg.trip_id,
               reg.boarding_stop_id, reg.dropoff_stop_id
        FROM registration reg
        JOIN passenger p ON p.pass_id=reg.pass_id
        JOIN trip t ON t.trip_id=reg.trip_id
        JOIN route r ON r.route_id=t.route_id
        LEFT JOIN stop sb ON sb.stop_id=reg.boarding_stop_id
        LEFT JOIN stop sd ON sd.stop_id=reg.dropoff_stop_id
        {where} ORDER BY t.trip_date DESC
    """))

@app.route("/api/registrations", methods=["POST"])
def api_regs_create():
    d = request.json
    nid = auto_id("registration","reg_id")
    execute_dml("""INSERT INTO registration(reg_id,status,pass_id,trip_id,boarding_stop_id,dropoff_stop_id)
        VALUES(%s,%s,%s,%s,%s,%s)""",
        (nid, d.get("status","Confirmed"), int(d["pass_id"]), int(d["trip_id"]),
         int(d["boarding_stop_id"]) if d.get("boarding_stop_id") else None,
         int(d["dropoff_stop_id"]) if d.get("dropoff_stop_id") else None))
    return ok("Registration created", id=nid), 201

@app.route("/api/registrations/<int:rid>", methods=["PUT"])
def api_regs_update(rid):
    d = request.json
    execute_dml("UPDATE registration SET status=%s WHERE reg_id=%s",(d["status"],rid))
    return ok("Status updated")

@app.route("/api/registrations/<int:rid>", methods=["DELETE"])
def api_regs_delete(rid):
    execute_dml("UPDATE registration SET status='Cancelled' WHERE reg_id=%s",(rid,))
    execute_dml("DELETE FROM registration WHERE reg_id=%s",(rid,))
    return ok("Registration deleted")

# ─── STOPS CRUD ───────────────────────────────────────────────────────────────
@app.route("/api/stops", methods=["GET"])
def api_stops_list():
    return jsonify(fetch_all("""
        SELECT s.stop_id, s.stop_name, s.address, s.site_name,
               COALESCE(si.site_type,'—') AS site_type,
               ROUND(s.latitude::numeric,5) AS lat,
               ROUND(s.longitude::numeric,5) AS lon,
               COUNT(DISTINCT rs.route_id) AS routes_count
        FROM stop s
        LEFT JOIN site si ON si.site_name=s.site_name
        LEFT JOIN route_stop rs ON rs.stop_id=s.stop_id
        GROUP BY s.stop_id,s.stop_name,s.address,s.site_name,si.site_type,s.latitude,s.longitude
        ORDER BY s.stop_id
    """))

@app.route("/api/stops/<int:sid>", methods=["GET"])
def api_stops_get(sid):
    r = fetch_one("SELECT * FROM stop WHERE stop_id=%s",(sid,))
    return jsonify(r) if r else abort(404)

@app.route("/api/stops", methods=["POST"])
def api_stops_create():
    d = request.json
    nid = auto_id("stop","stop_id")
    execute_dml("INSERT INTO stop(stop_id,stop_name,address,latitude,longitude,site_name) VALUES(%s,%s,%s,%s,%s,%s)",
                (nid,d["stop_name"],d["address"],float(d["lat"]),float(d["lon"]),d["site_name"]))
    return ok("Stop created", id=nid), 201

@app.route("/api/stops/<int:sid>", methods=["PUT"])
def api_stops_update(sid):
    d = request.json
    execute_dml("UPDATE stop SET stop_name=%s,address=%s,latitude=%s,longitude=%s,site_name=%s WHERE stop_id=%s",
                (d["stop_name"],d["address"],float(d["lat"]),float(d["lon"]),d["site_name"],sid))
    return ok("Stop updated")

@app.route("/api/stops/<int:sid>", methods=["DELETE"])
def api_stops_delete(sid):
    execute_dml("UPDATE registration SET boarding_stop_id=NULL WHERE boarding_stop_id=%s",(sid,))
    execute_dml("UPDATE registration SET dropoff_stop_id=NULL WHERE dropoff_stop_id=%s",(sid,))
    execute_dml("DELETE FROM route_stop WHERE stop_id=%s",(sid,))
    execute_dml("DELETE FROM stop WHERE stop_id=%s",(sid,))
    return ok("Stop deleted")

# ─── QUERIES & PROCEDURES ─────────────────────────────────────────────────────
@app.route("/api/query/routes_dashboard", methods=["POST"])
def q_routes_dashboard():
    return jsonify(fetch_all("""
        SELECT r.route_id, r.route_name, reg.regio_name,
               r.estimated_duration_minutes, r.total_distance_km,
               COUNT(rs.stop_id) AS total_stops
        FROM route r
        JOIN region reg ON r.region_id=reg.region_id
        LEFT JOIN route_stop rs ON r.route_id=rs.route_id
        GROUP BY r.route_id,r.route_name,reg.regio_name,
                 r.estimated_duration_minutes,r.total_distance_km
        ORDER BY r.route_id
    """))

@app.route("/api/query/region_stats", methods=["POST"])
def q_region_stats():
    return jsonify(fetch_all("""
        SELECT reg.regio_name, reg.terrain_type,
               COUNT(r.route_id) AS routes_count,
               ROUND(AVG(r.estimated_duration_minutes),2) AS avg_duration,
               ROUND(AVG(r.total_distance_km)::numeric,2) AS avg_distance
        FROM region reg JOIN route r ON reg.region_id=r.region_id
        GROUP BY reg.regio_name,reg.terrain_type
        HAVING COUNT(r.route_id)>0 ORDER BY avg_duration DESC
    """))

@app.route("/api/query/route_stops", methods=["POST"])
def q_route_stops():
    rid = request.json.get("route_id")
    return jsonify(fetch_all("""
        SELECT r.route_name, rs.stop_order, s.stop_name, s.address,
               rs.estimated_arrival_time::text AS estimated_arrival_time,
               si.site_name, si.site_type
        FROM route_stop rs
        JOIN route r ON rs.route_id = r.route_id
        JOIN stop s ON rs.stop_id = s.stop_id
        JOIN site si ON s.site_name = si.site_name
        WHERE r.route_id = %s
        ORDER BY rs.stop_order
    """, (int(rid),)))

@app.route("/api/query/schedule_range", methods=["POST"])
def q_schedule_range():
    d = request.json
    return jsonify(fetch_all("""
        SELECT t.trip_id, t.trip_date::text AS trip_date, t.departure_time, r.route_name,
               v.plate_number, v.vehicle_type, t.available_seats
        FROM trip t
        JOIN route r ON t.route_id = r.route_id
        JOIN vehicle v ON t.plate_number = v.plate_number
        WHERE t.trip_date BETWEEN %s::date AND %s::date
        ORDER BY t.trip_date, t.departure_time
    """, (d["start_date"], d["end_date"])))

@app.route("/api/query/trip_occupancy_summary", methods=["POST"])
def q_trip_occupancy_summary():
    tid = request.json.get("trip_id")
    return jsonify(fetch_all("""
        SELECT t.trip_id, r.route_name, t.trip_date::text AS trip_date, t.departure_time,
               v.plate_number, v.vehicle_type, v.capacity, t.available_seats,
               (v.capacity - t.available_seats) AS occupied_seats,
               ROUND(((v.capacity - t.available_seats)::numeric / NULLIF(v.capacity,0)) * 100, 2) AS occupancy_percent
        FROM trip t
        JOIN route r ON t.route_id = r.route_id
        JOIN vehicle v ON t.plate_number = v.plate_number
        WHERE t.trip_id = %s
    """, (int(tid),)))

@app.route("/api/query/active_vehicles", methods=["POST"])
def q_active_vehicles():
    min_trips = request.json.get("min_trips", 5)
    return jsonify(fetch_all("""
        SELECT v.plate_number, v.vehicle_type, v.capacity,
               COUNT(t.trip_id) AS total_trips
        FROM vehicle v
        JOIN trip t ON v.plate_number = t.plate_number
        GROUP BY v.plate_number, v.vehicle_type, v.capacity
        HAVING COUNT(t.trip_id) >= %s
        ORDER BY total_trips DESC
    """, (int(min_trips),)))

@app.route("/api/query/peak_days", methods=["GET"])
def q_peak_days():
    return jsonify(fetch_all("""
        SELECT EXTRACT(YEAR FROM trip_date)::int AS trip_year,
               EXTRACT(MONTH FROM trip_date)::int AS trip_month,
               EXTRACT(DAY FROM trip_date)::int AS trip_day,
               COUNT(*) AS total_trips
        FROM trip
        GROUP BY EXTRACT(YEAR FROM trip_date),
                 EXTRACT(MONTH FROM trip_date),
                 EXTRACT(DAY FROM trip_date)
        ORDER BY total_trips DESC
        LIMIT 15
    """))

@app.route("/api/proc/route_dashboard", methods=["POST"])
def p_route_dashboard():
    try:
        rows = call_refcursor_function("SELECT get_route_dashboard()",
                                       'FETCH ALL FROM "route_dashboard_cursor"')
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/proc/trip_occupancy", methods=["POST"])
def p_trip_occupancy():
    tid = request.json.get("trip_id")
    try:
        rows = call_table_function("calculate_trip_occupancy(%s)",(int(tid),))
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/proc/schedule_trip", methods=["POST"])
def p_schedule_trip():
    d = request.json
    try:
        nid = auto_id("trip","trip_id")
        call_procedure("schedule_new_trip",(
            nid, int(d["route_id"]), d["trip_date"], d["departure_time"],
            int(d.get("expected_pass",0)), d["plate_number"],
            int(d["driver_id"]) if d.get("driver_id") else None,
        ))
        return ok(f"Trip scheduled! ID: {nid}", id=nid)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/proc/auto_assign", methods=["POST"])
def p_auto_assign():
    try:
        call_procedure("auto_assign_drivers_to_future_trips",[])
        rows = fetch_all("""
            SELECT t.trip_id, t.trip_date, r.route_name, d.driver_fullname AS driver_name
            FROM trip t JOIN route r ON r.route_id=t.route_id
            JOIN driver d ON d.driver_id=t.driver_id
            WHERE t.trip_date>=CURRENT_DATE ORDER BY t.trip_date LIMIT 20
        """)
        return jsonify({"message":"Drivers assigned!", "trips": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── MAINTENANCE (Phase 2 UPDATE / DELETE QUERIES) ────────────────────────────
@app.route("/api/maintenance/close_past_trips", methods=["POST"])
def m_close_past_trips():
    c = execute_dml("UPDATE trip SET available_seats = 0 WHERE trip_date < CURRENT_DATE AND available_seats > 0")
    return ok(f"Closed {c} past trips successfully")

@app.route("/api/maintenance/adjust_long_routes", methods=["POST"])
def m_adjust_long_routes():
    c = execute_dml("UPDATE route SET estimated_duration_minutes = estimated_duration_minutes + 15 WHERE total_distance_km > 150")
    return ok(f"Adjusted duration for {c} long routes")

@app.route("/api/maintenance/cleanup_old_trips", methods=["POST"])
def m_cleanup_old_trips():
    try:
        execute_dml("DELETE FROM registration WHERE trip_id IN (SELECT trip_id FROM trip WHERE trip_date < CURRENT_DATE AND available_seats = 0)")
        c = execute_dml("DELETE FROM trip WHERE trip_date < CURRENT_DATE AND available_seats = 0")
        return ok(f"Deleted {c} old full trips")
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ─── Launch ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("TransRoute Planner running at http://localhost:5000")
    app.run(debug=True, port=5000)
