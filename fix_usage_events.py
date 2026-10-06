import psycopg2

db_url_line = [line for line in open('.env') if line.startswith('DATABASE_URL=')][0].strip()
db_url = db_url_line.split('=', 1)[1].strip('"').strip("'")
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS usage_events CASCADE;")
cur.execute("""
    CREATE TABLE usage_events (
        event_id VARCHAR(50) PRIMARY KEY,
        tenant_id VARCHAR(50) NOT NULL,
        event_type VARCHAR(50) NOT NULL,
        api_call VARCHAR(100),
        llm_tokens INTEGER DEFAULT 0,
        store_id VARCHAR(50),
        quantity INTEGER DEFAULT 1,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
print("Fixed usage_events table.")
cur.close()
conn.close()
