"""Load labelled synthetic returns into the v1.1 PostgreSQL returns table."""

from __future__ import annotations

import csv
import hashlib
import sys
from collections import Counter
from pathlib import Path


RETURNS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = RETURNS_DIR.parents[1]
CSV_PATH = RETURNS_DIR / "returns.csv"


def get_database_url() -> str:
    import os

    value = os.environ.get("DATABASE_URL")
    if value:
        return value
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "postgresql://postgres:postgres@localhost:5432/retail"


def load_returns(database_url: str | None = None, csv_path: Path = CSV_PATH) -> None:
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        print("SQLAlchemy is required to load returns.")
        raise

    with csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    query = text("""
        INSERT INTO returns (
            return_id, tenant_id, product_id, supplier_id, batch_id, courier,
            store_id, customer_ref_hash, raw_text_enc, clean_text, issue,
            root_cause_gold, order_value_lkr, purchase_date, return_date, district
        ) VALUES (
            :return_id, 'demo', :product_id, :supplier_id, :batch_id, :courier,
            :store_id, :customer_ref_hash, :raw_text_enc, :clean_text, :issue,
            :root_cause_gold, :order_value_lkr, :purchase_date, :return_date, :district
        )
        ON CONFLICT (return_id) DO UPDATE SET
            product_id = EXCLUDED.product_id,
            supplier_id = EXCLUDED.supplier_id,
            batch_id = EXCLUDED.batch_id,
            courier = EXCLUDED.courier,
            store_id = EXCLUDED.store_id,
            customer_ref_hash = EXCLUDED.customer_ref_hash,
            raw_text_enc = EXCLUDED.raw_text_enc,
            clean_text = EXCLUDED.clean_text,
            issue = EXCLUDED.issue,
            root_cause_gold = EXCLUDED.root_cause_gold,
            order_value_lkr = EXCLUDED.order_value_lkr,
            purchase_date = EXCLUDED.purchase_date,
            return_date = EXCLUDED.return_date,
            district = EXCLUDED.district;
    """)
    engine = create_engine(database_url or get_database_url())
    with engine.begin() as connection:
        for row in rows:
            customer_hash = hashlib.sha256(row["customer_ref"].encode("utf-8")).hexdigest()
            connection.execute(query, {
                "return_id": row["return_id"], "product_id": row["product_id"],
                "supplier_id": row["supplier_id"], "batch_id": row["batch_id"],
                "courier": row["courier"], "store_id": row["store_id"],
                "customer_ref_hash": customer_hash, "raw_text_enc": None,
                "clean_text": row["text"], "issue": row["text"],
                "root_cause_gold": row["root_cause_label"],
                "order_value_lkr": float(row["order_value_lkr"]),
                "purchase_date": row["purchase_date"], "return_date": row["return_date"],
                "district": row["district"],
            })
    print(f"Loaded {len(rows)} returns from {csv_path.name}")
    print("Class counts:", dict(Counter(row["root_cause_label"] for row in rows)))


if __name__ == "__main__":
    load_returns(sys.argv[1] if len(sys.argv) > 1 else None)