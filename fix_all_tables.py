import psycopg2

db_url_line = [line for line in open('.env') if line.startswith('DATABASE_URL=')][0].strip()
db_url = db_url_line.split('=', 1)[1].strip('"').strip("'")
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE bulk_jobs ADD COLUMN user_id VARCHAR(50);")
    cur.execute("ALTER TABLE bulk_jobs ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;")
except Exception as e:
    print(e)
    
try:
    cur.execute("ALTER TABLE returns ADD COLUMN bulk_job_id VARCHAR(100);")
except Exception as e:
    print(e)
    
try:
    cur.execute("ALTER TABLE decisions ADD COLUMN bulk_job_id VARCHAR(100);")
except Exception as e:
    print(e)

print("Added columns")
cur.close()
conn.close()
