"""
Script to load catalogue CSV files into PostgreSQL.
Safe to run multiple times (idempotent via ON CONFLICT upsert).
"""
import csv
import os
import sys
from pathlib import Path

CATALOG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CATALOG_DIR.parent.parent


def get_database_url() -> str:
    """Resolve database URL from environment or .env file."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    if not db_url:
        # Fallback to local default if not set
        db_url = "postgresql://postgres:postgres@localhost:5432/retail"
    return db_url


def load_suppliers(engine):
    from sqlalchemy import text
    filepath = CATALOG_DIR / "suppliers.csv"
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    query = text("""
        INSERT INTO suppliers (supplier_id, name, country, quality_tier)
        VALUES (:supplier_id, :name, :country, :quality_tier)
        ON CONFLICT (supplier_id) DO UPDATE SET
            name = EXCLUDED.name,
            country = EXCLUDED.country,
            quality_tier = EXCLUDED.quality_tier;
    """)

    with engine.begin() as conn:
        for r in rows:
            conn.execute(query, {
                "supplier_id": r["supplier_id"],
                "name": r["name"],
                "country": r["country"],
                "quality_tier": r["quality_tier"],
            })
    print(f"Loaded {len(rows)} suppliers from {filepath.name}")


def load_return_policies(engine):
    from sqlalchemy import text
    filepath = CATALOG_DIR / "return_policies.csv"
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    query = text("""
        INSERT INTO return_policies (category, window_days, non_returnable_unless_defective)
        VALUES (:category, :window_days, :non_returnable_unless_defective)
        ON CONFLICT (category) DO UPDATE SET
            window_days = EXCLUDED.window_days,
            non_returnable_unless_defective = EXCLUDED.non_returnable_unless_defective;
    """)

    with engine.begin() as conn:
        for r in rows:
            conn.execute(query, {
                "category": r["category"],
                "window_days": int(r["window_days"]),
                "non_returnable_unless_defective": r["non_returnable_unless_defective"].lower() == "true",
            })
    print(f"Loaded {len(rows)} return policies from {filepath.name}")


def load_products(engine):
    from sqlalchemy import text
    filepath = CATALOG_DIR / "products.csv"
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    query = text("""
        INSERT INTO products (product_id, name, brand, category, price_lkr, supplier_id, return_window_days)
        VALUES (:product_id, :name, :brand, :category, :price_lkr, :supplier_id, :return_window_days)
        ON CONFLICT (product_id) DO UPDATE SET
            name = EXCLUDED.name,
            brand = EXCLUDED.brand,
            category = EXCLUDED.category,
            price_lkr = EXCLUDED.price_lkr,
            supplier_id = EXCLUDED.supplier_id,
            return_window_days = EXCLUDED.return_window_days;
    """)

    with engine.begin() as conn:
        for r in rows:
            conn.execute(query, {
                "product_id": r["product_id"],
                "name": r["name"],
                "brand": r["brand"],
                "category": r["category"],
                "price_lkr": float(r["price_lkr"]),
                "supplier_id": r["supplier_id"],
                "return_window_days": int(r["return_window_days"]),
            })
    print(f"Loaded {len(rows)} products from {filepath.name}")


def load_all(database_url: str | None = None):
    try:
        from sqlalchemy import create_engine
    except ImportError:
        print("SQLAlchemy is required to load into Postgres. Install with: pip install sqlalchemy psycopg2-binary")
        sys.exit(1)

    url = database_url or get_database_url()
    print(f"Connecting to database: {url.split('@')[-1] if '@' in url else url}")
    engine = create_engine(url)
    load_suppliers(engine)
    load_return_policies(engine)
    load_products(engine)
    print("Catalogue load completed successfully.")


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    load_all(url_arg)
