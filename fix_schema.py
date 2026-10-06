import os
import psycopg2
from urllib.parse import urlparse

db_url_line = [line for line in open('.env') if line.startswith('DATABASE_URL=')][0].strip()
db_url = db_url_line.split('=', 1)[1].strip('"').strip("'")
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE suppliers ADD CONSTRAINT unique_supplier_id UNIQUE (supplier_id);")
    print("Added unique constraint to supplier_id")
except Exception as e:
    print(f"Constraint might already exist or error: {e}")

try:
    cur.execute("ALTER TABLE products ADD CONSTRAINT unique_product_id UNIQUE (product_id);")
    print("Added unique constraint to product_id")
except Exception as e:
    pass
    
cur.close()
conn.close()
