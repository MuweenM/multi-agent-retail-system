"""
Unit tests for data catalog, SQL migrations, planted test story, and .env.example.
"""
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CATALOG_DIR = DATA_DIR / "catalog"


def test_products_csv_structure_and_counts():
    products_file = CATALOG_DIR / "products.csv"
    assert products_file.exists(), "products.csv does not exist"

    with open(products_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 40, f"Expected 40 products, found {len(reader)}"

    expected_ids = [f"P-{i:03d}" for i in range(1, 41)]
    actual_ids = [r["product_id"] for r in reader]
    assert actual_ids == expected_ids, "Product IDs must strictly be P-001 through P-040"

    # Category breakdown: 10 electronics, 12 fashion, 10 home, 8 packaged grocery
    category_counts = {}
    for r in reader:
        cat = r["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    assert category_counts.get("electronics") == 10, f"Expected 10 electronics, got {category_counts.get('electronics')}"
    assert category_counts.get("fashion") == 12, f"Expected 12 fashion, got {category_counts.get('fashion')}"
    assert category_counts.get("home") == 10, f"Expected 10 home, got {category_counts.get('home')}"
    assert category_counts.get("grocery") == 8, f"Expected 8 grocery, got {category_counts.get('grocery')}"

    # Pinned product verifications
    p_by_id = {r["product_id"]: r for r in reader}

    # P-009 wireless earbuds
    p009 = p_by_id["P-009"]
    assert "earbuds" in p009["name"].lower()
    assert p009["category"] == "electronics"

    # P-014 20,000 mAh power bank (supplier S-03)
    p014 = p_by_id["P-014"]
    assert "power bank" in p014["name"].lower()
    assert "20000" in p014["name"] or "20,000" in p014["name"]
    assert p014["supplier_id"] == "S-03"
    assert p014["category"] == "electronics"

    # P-027 slim-fit cotton shirt (supplier S-05)
    p027 = p_by_id["P-027"]
    assert "shirt" in p027["name"].lower()
    assert "slim" in p027["name"].lower()
    assert p027["supplier_id"] == "S-05"
    assert p027["category"] == "fashion"


def test_suppliers_csv():
    suppliers_file = CATALOG_DIR / "suppliers.csv"
    assert suppliers_file.exists(), "suppliers.csv does not exist"

    with open(suppliers_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 8, f"Expected 8 suppliers, got {len(reader)}"
    supplier_ids = [r["supplier_id"] for r in reader]
    expected_ids = [f"S-0{i}" for i in range(1, 9)]
    assert supplier_ids == expected_ids

    # S-03 and S-05 must be present
    s_map = {r["supplier_id"]: r for r in reader}
    assert s_map["S-03"]["quality_tier"] in ["Tier-1", "Tier-2", "Tier-3"]
    assert s_map["S-05"]["quality_tier"] in ["Tier-1", "Tier-2", "Tier-3"]


def test_return_policies_csv():
    policy_file = CATALOG_DIR / "return_policies.csv"
    assert policy_file.exists(), "return_policies.csv does not exist"

    with open(policy_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    policy_map = {r["category"]: r for r in reader}
    assert set(policy_map.keys()) == {"electronics", "fashion", "home", "grocery"}

    assert int(policy_map["electronics"]["window_days"]) == 14
    assert policy_map["electronics"]["non_returnable_unless_defective"].lower() == "false"

    assert int(policy_map["fashion"]["window_days"]) == 14
    assert policy_map["fashion"]["non_returnable_unless_defective"].lower() == "false"

    assert int(policy_map["home"]["window_days"]) == 7
    assert policy_map["home"]["non_returnable_unless_defective"].lower() == "false"

    assert int(policy_map["grocery"]["window_days"]) == 2
    assert policy_map["grocery"]["non_returnable_unless_defective"].lower() == "true"


def test_planted_md():
    planted_file = DATA_DIR / "PLANTED.md"
    assert planted_file.exists(), "data/PLANTED.md does not exist"

    content = planted_file.read_text(encoding="utf-8")
    assert "DATASET_TODAY" in content

    # 5 planted patterns word for word
    assert "a. P-014 from S-03, batch B-2026-07: battery swelling, a manufacturing_defect spike in the last 3 weeks." in content
    assert "b. P-027: \"runs small\", size_fit_issue across all suppliers and batches." in content
    assert "c. Courier C-2: a one-week spike of damaged_in_transit on electronics." in content
    assert "d. 12 pseudonymous customers with 6 or more returns in 60 days, mostly change_of_mind on high-value items (policy_abuse_suspected candidates)." in content
    assert "e. P-009: reviews praise \"great battery life\" (a keyword distractor), while its returns are mostly not_as_described because the listing claimed noise cancelling." in content


def test_migration_sql():
    sql_file = PROJECT_ROOT / "infra" / "postgres" / "migrations" / "001_v11.sql"
    assert sql_file.exists(), "001_v11.sql migration does not exist"

    sql = sql_file.read_text(encoding="utf-8")
    for tbl in ["products", "suppliers", "return_policies", "returns", "decisions", "bulk_jobs", "tenants", "users", "audit_log", "usage_events"]:
        assert tbl in sql, f"Table {tbl} missing in migration SQL"

    # returns columns
    for col in [
        "return_id", "tenant_id", "job_id", "product_id", "supplier_id", "batch_id",
        "courier", "store_id", "customer_ref_hash", "raw_text_enc", "clean_text",
        "issue", "root_cause_pred", "root_cause_gold", "order_value_lkr",
        "purchase_date", "return_date", "district", "created_at"
    ]:
        assert col in sql, f"Column {col} missing in returns schema"

    # Index on (tenant_id, product_id, return_date)
    assert "(tenant_id, product_id, return_date)" in sql


def test_env_example_keys():
    env_file = PROJECT_ROOT / ".env.example"
    assert env_file.exists(), ".env.example does not exist"

    content = env_file.read_text(encoding="utf-8")
    required_keys = [
        "DATASET_TODAY",
        "PSEUDONYM_KEY",
        "ENCRYPTION_KEY",
        "SERVICE_SECRET",
        "ENABLE_SI=false",
        "HUMAN_REVIEW_MIN_CONFIDENCE=0.75",
        "HIGH_VALUE_LKR=100000",
        "LLM_MAX_CALLS_PER_BULK_JOB=100",
    ]
    for key in required_keys:
        assert key in content, f"Missing key in .env.example: {key}"
