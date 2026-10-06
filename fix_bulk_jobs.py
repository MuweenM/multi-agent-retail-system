import psycopg2

db_url_line = [line for line in open('.env') if line.startswith('DATABASE_URL=')][0].strip()
db_url = db_url_line.split('=', 1)[1].strip('"').strip("'")
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS bulk_jobs CASCADE;")
cur.execute("""
    CREATE TABLE bulk_jobs (
        job_id VARCHAR(100) PRIMARY KEY,
        tenant_id VARCHAR(50) NOT NULL,
        status VARCHAR(50) NOT NULL DEFAULT 'queued',
        total_rows INT NOT NULL DEFAULT 0,
        processed_rows INT NOT NULL DEFAULT 0,
        failed_rows INT NOT NULL DEFAULT 0,
        summary_json JSONB DEFAULT '[]'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
""")
print("Fixed bulk_jobs table.")
cur.close()
conn.close()
