"""Generate sample CSV with 200 rows including 10 intentional errors (Prompt 1.5 requirement)."""

import csv
import os
import random

PRODUCTS = [
    ("P-001", "Galaxy A15 Smartphone", "45000"),
    ("P-009", "True Wireless Earbuds Pro", "14500"),
    ("P-014", "20000mAh Fast Charging Power Bank", "9200"),
    ("P-027", "Slim-Fit Cotton Dress Shirt", "4800"),
    ("P-028", "Non-Stick Fry Pan 24cm", "5800"),
    ("P-033", "Ceylon Premium Black Tea 500g", "1850"),
]

ISSUES = [
    "Battery drains in less than 2 hours, please replace",
    "Screen flickering intermittently after charging",
    "Size XL runs very small compared to regular sizing",
    "Noise cancellation does not work as advertised",
    "Coating peeling off after two gentle washes",
    "Packet seal was broken when courier delivered package",
    "Charger port feels loose and does not fast charge",
    "Phone heats up excessively during normal voice calls",
]


def generate_sample_csv():
    random.seed(101)
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "returns_sample.csv"))

    rows = []
    # 190 valid rows
    for i in range(1, 191):
        pid, name, price = random.choice(PRODUCTS)
        issue = random.choice(ISSUES)
        rows.append({
            "return_id": f"RET-{i:05d}",
            "text": f"Bought {name} ({pid}). {issue}. Order ORD-{1000 + i}, contact 077{random.randint(1000000, 9999999)}",
            "order_id": f"ORD-{1000 + i}",
            "product_id": pid,
            "customer_ref": f"CUST-USER-{random.randint(1, 40):03d}",
            "order_value_lkr": price,
            "purchase_date": "2026-08-15",
            "return_date": "2026-08-22",
            "store_id": f"STORE-{random.randint(1, 5):02d}",
            "courier": f"C-{random.randint(1, 3)}",
        })

    # 10 intentional error/edge-case rows
    error_cases = [
        {"return_id": "RET-00191", "text": "", "order_id": "ORD-1191", "product_id": "P-001", "customer_ref": "c1", "order_value_lkr": "45000", "purchase_date": "2026-08-15", "return_date": "2026-08-22", "store_id": "STORE-01", "courier": "C-1"},
        {"return_id": "RET-00192", "text": "   ", "order_id": "ORD-1192", "product_id": "P-002", "customer_ref": "c2", "order_value_lkr": "38000", "purchase_date": "2026-08-15", "return_date": "2026-08-22", "store_id": "STORE-01", "courier": "C-1"},
        {"return_id": "RET-00193", "text": "Extremely long complaint " + ("very bad defect " * 250), "order_id": "ORD-1193", "product_id": "P-014", "customer_ref": "c3", "order_value_lkr": "9200", "purchase_date": "2026-08-15", "return_date": "2026-08-22", "store_id": "STORE-01", "courier": "C-1"},
        {"return_id": "RET-00194", "text": "=SUM(A1:A10) broken phone", "order_id": "ORD-1194", "product_id": "P-001", "customer_ref": "c4", "order_value_lkr": "45000", "purchase_date": "2026-08-15", "return_date": "2026-08-22", "store_id": "STORE-01", "courier": "C-1"},
        {"return_id": "RET-00195", "text": "+123456789 formula injection test", "order_id": "ORD-1195", "product_id": "P-001", "customer_ref": "c5", "order_value_lkr": "45000", "purchase_date": "2026-08-15", "return_date": "2026-08-22", "store_id": "STORE-01", "courier": "C-1"},
        {"return_id": "RET-00196", "text": "-CMD /c calc.exe defect", "order_id": "ORD-1196", "product_id": "P-001", "customer_ref": "c6", "order_value_lkr": "45000", "purchase_date": "2026-08-15", "return_date": "2026-08-22", "store_id": "STORE-01", "courier": "C-1"},
        {"return_id": "RET-00197", "text": "@SUM(1+1) power bank died", "order_id": "ORD-1197", "product_id": "P-014", "customer_ref": "c7", "order_value_lkr": "9200", "purchase_date": "2026-08-15", "return_date": "2026-08-22", "store_id": "STORE-01", "courier": "C-1"},
        {"return_id": "RET-00198", "text": "Broken tea box", "order_id": "ORD-1198", "product_id": "P-033", "customer_ref": "c8", "order_value_lkr": "INVALID_PRICE", "purchase_date": "2026-08-15", "return_date": "2026-08-22", "store_id": "STORE-01", "courier": "C-1"},
        {"return_id": "RET-00199", "text": "Wrong color delivered", "order_id": "ORD-1199", "product_id": "P-027", "customer_ref": "c9", "order_value_lkr": "NOT_A_NUMBER", "purchase_date": "2026-08-15", "return_date": "2026-08-22", "store_id": "STORE-01", "courier": "C-1"},
        {"return_id": "RET-00200", "text": "", "order_id": "ORD-1200", "product_id": "P-028", "customer_ref": "c10", "order_value_lkr": "5800", "purchase_date": "2026-08-15", "return_date": "2026-08-22", "store_id": "STORE-01", "courier": "C-1"},
    ]
    rows.extend(error_cases)

    fieldnames = ["return_id", "text", "order_id", "product_id", "customer_ref", "order_value_lkr", "purchase_date", "return_date", "store_id", "courier"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated 200 sample returns (190 valid, 10 error cases) at: {output_path}")


if __name__ == "__main__":
    generate_sample_csv()
