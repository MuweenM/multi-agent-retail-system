import os
import psycopg2

db_url_line = [line for line in open('.env') if line.startswith('DATABASE_URL=')][0].strip()
db_url = db_url_line.split('=', 1)[1].strip('"').strip("'")
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE suppliers DROP COLUMN IF EXISTS product;")
    cur.execute("ALTER TABLE suppliers DROP COLUMN IF EXISTS quality_flag;")
    print("Dropped legacy columns from suppliers table")
except Exception as e:
    print(f"Error dropping columns: {e}")
    
cur.close()
conn.close()
