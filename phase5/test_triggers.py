from db_connection import fetch_all
print(fetch_all("SELECT tgname, proname FROM pg_trigger JOIN pg_proc ON pg_trigger.tgfoid = pg_proc.oid;"))
