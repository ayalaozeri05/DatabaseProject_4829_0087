from db_connection import fetch_one
print(fetch_one("SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname = 'trg_registration_after_insert';"))
