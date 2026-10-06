import os
import psycopg2
from urllib.parse import urlparse

db_url_line = [line for line in open('.env') if line.startswith('DATABASE_URL=')][0].strip()
db_url = db_url_line.split('=', 1)[1].strip('"').strip("'")
print(f"Connecting to {db_url}...")

conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

for filepath in ["infra/postgres/init.sql", "infra/postgres/migrations/001_v11.sql"]:
    if os.path.exists(filepath):
        print(f"Executing {filepath}...")
        with open(filepath, 'r') as f:
            sql = f.read()
            if sql.strip():
                cur.execute(sql)
                print(f"Success for {filepath}")
    else:
        print(f"File {filepath} not found!")

cur.close()
conn.close()
