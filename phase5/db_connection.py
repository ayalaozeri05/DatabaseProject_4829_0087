import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

# Load .env dynamically
def _load_env():
    # .env is in the parent directory of phase5
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    env_data = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.strip().split("=", 1)
                        env_data[k.strip()] = v.strip()
        except Exception as e:
            print(f"Warning: could not read .env: {e}")
    return env_data

_env = _load_env()

# ─── DB Config (matches .env / docker-compose) ───────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "port": int(_env.get("DB_PORT", 5433)),
    "database": _env.get("DB_NAME_SECRET", "finalll_integration"),
    "user": _env.get("DB_USER_SECRET", "ayala"),
    "password": _env.get("DB_PASSWORD_SECRET", "ayala"),
}


def get_connection():
    """Return a new psycopg2 connection."""
    return psycopg2.connect(**DB_CONFIG)


@contextmanager
def db_cursor(commit=False):
    """Context manager yielding a DictCursor; optionally commits on exit."""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur, conn
        if commit:
            conn.commit()
        else:
            conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def test_connection():
    """Return True if DB is reachable."""
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception as e:
        return str(e)


# ─── Generic helpers ─────────────────────────────────────────────────────────

def fetch_all(query: str, params=None):
    with db_cursor() as (cur, _):
        cur.execute(query, params or ())
        return [dict(r) for r in cur.fetchall()]


def fetch_one(query: str, params=None):
    with db_cursor() as (cur, _):
        cur.execute(query, params or ())
        row = cur.fetchone()
        return dict(row) if row else None


def execute_dml(query: str, params=None):
    """Execute INSERT/UPDATE/DELETE and commit. Returns rowcount."""
    with db_cursor(commit=True) as (cur, _):
        cur.execute(query, params or ())
        return cur.rowcount


def call_procedure(name: str, params=None):
    """CALL a stored procedure (no return value)."""
    with db_cursor(commit=True) as (cur, _):
        if params:
            placeholders = ", ".join(["%s"] * len(params))
            cur.execute(f"CALL {name}({placeholders})", params)
        else:
            cur.execute(f"CALL {name}()")


def call_refcursor_function(func_sql: str, fetch_sql: str):
    """
    Run a refcursor function inside a transaction and FETCH ALL results.
    func_sql  – e.g. "SELECT get_route_dashboard()"
    fetch_sql – e.g. 'FETCH ALL FROM "route_dashboard_cursor"'
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(func_sql)
        cur.execute(fetch_sql)
        rows = [dict(r) for r in cur.fetchall()]
        conn.commit()
        return rows
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def call_table_function(func_call: str, params=None):
    """SELECT * FROM table_function(...)."""
    with db_cursor() as (cur, _):
        cur.execute(f"SELECT * FROM {func_call}", params or ())
        return [dict(r) for r in cur.fetchall()]


# ─── Lookup helpers (used by dropdowns) ──────────────────────────────────────

def get_regions():
    return fetch_all("SELECT region_id, regio_name FROM region ORDER BY regio_name")


def get_routes():
    return fetch_all("SELECT route_id, route_name FROM route ORDER BY route_name")


def get_vehicles():
    return fetch_all("SELECT plate_number, vehicle_type, capacity FROM vehicle ORDER BY plate_number")


def get_drivers():
    return fetch_all("SELECT driver_id, driver_fullname FROM driver ORDER BY driver_fullname")


def get_passengers():
    return fetch_all("SELECT pass_id, pass_fullname FROM passenger ORDER BY pass_fullname")


def get_stops():
    return fetch_all("SELECT stop_id, stop_name FROM stop ORDER BY stop_name")


def get_sites():
    return fetch_all("SELECT site_name FROM site ORDER BY site_name")


def get_trips():
    return fetch_all(
        """SELECT t.trip_id,
                  t.trip_date::text || ' ' || t.departure_time AS label
           FROM trip t ORDER BY t.trip_date DESC, t.departure_time"""
    )
