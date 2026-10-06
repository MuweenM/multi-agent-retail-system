import os
import psycopg2

db_url_line = [line for line in open('.env') if line.startswith('DATABASE_URL=')][0].strip()
db_url = db_url_line.split('=', 1)[1].strip('"').strip("'")
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE returns ADD CONSTRAINT unique_return_id UNIQUE (return_id);")
except Exception as e:
    pass

try:
    cur.execute("ALTER TABLE returns DROP COLUMN IF EXISTS product;")
    cur.execute("ALTER TABLE returns DROP COLUMN IF EXISTS raw_text;")
except Exception as e:
    pass

cur.close()
conn.close()
