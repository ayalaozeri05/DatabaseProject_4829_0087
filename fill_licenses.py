import sys
sys.path.append('phase5')
from db_connection import execute_dml

sql = """
UPDATE driver 
SET licensetype = (ARRAY['B', 'C', 'C1', 'D', 'D1', 'D2', 'D3'])[floor(random() * 7 + 1)]
WHERE licensetype IS NULL;
"""
res = execute_dml(sql)
print(f"Updated {res} driver license types.")
