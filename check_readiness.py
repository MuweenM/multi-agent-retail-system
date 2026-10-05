import psycopg2

db_url_line = [line for line in open('.env') if line.startswith('DATABASE_URL=')][0].strip()
db_url = db_url_line.split('=', 1)[1].strip('"').strip("'")
conn = psycopg2.connect(db_url)
cur = conn.cursor()

print("1. Raw connectivity check:")
cur.execute("SELECT 1;")
print(f"select 1 returned: {cur.fetchone()[0]}")

print("\n3. Schema check (tables in public):")
cur.execute("select table_name from information_schema.tables where table_schema='public';")
tables = [row[0] for row in cur.fetchall()]
print(tables)

print("\n4. Catalogue data load check (products count):")
cur.execute("SELECT COUNT(*) FROM products;")
print(f"Products count: {cur.fetchone()[0]}")

print("\n5. Returns data load check (returns count):")
cur.execute("SELECT COUNT(*) FROM returns;")
print(f"Returns count: {cur.fetchone()[0]}")

cur.close()
conn.close()
