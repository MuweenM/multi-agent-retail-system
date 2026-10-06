from __future__ import annotations

import csv
import json
import os
import random
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.retail_common.taxonomy import ROOT_CAUSES, SOURCE_TYPES

SEED = 20260925
LLM_BATCH_SIZE = 20
DATA_DIR = ROOT / "data"
RETURNS_PATH = DATA_DIR / "returns" / "returns.csv"
PRODUCTS_PATH = DATA_DIR / "catalog" / "products.csv"
OUTPUT_PATH = DATA_DIR / "corpus" / "corpus.jsonl"
README_PATH = DATA_DIR / "corpus" / "README.md"


def dataset_today() -> date:
    env_path = ROOT / ".env"
    value = ""
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATASET_TODAY="):
                value = line.split("=", 1)[1].strip()
                break
    if not value:
        value = "2026-09-22"
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_products() -> list[dict[str, str]]:
    with PRODUCTS_PATH.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _llm_expand_rows(rows: list[dict[str, Any]], source_type: str, rng: random.Random) -> list[dict[str, Any]]:
    try:
        from shared.retail_common.llm_client import call_llm
    except Exception:
        return rows

    prompt_lines = []
    for row in rows:
        prompt_lines.append(
            f"{row['id']}|{row['source_type']}|{row['title']}|{row['body']}|{row['product_id']}|{row['supplier_id']}|{row['batch_id']}|{row.get('label_hint') or 'null'}"
        )
    prompt = (
        "Rewrite the following synthetic retail snippets in more natural, varied English while preserving the product, supplier, batch, and issue intent. "
        "Keep the exact product identifiers and source types. Return each item as 'id|title|body|label_hint'.\n"
        + "\n".join(prompt_lines)
    )
    try:
        response = call_llm(prompt, system="You generate synthetic customer and supplier text for retail evaluation data.", max_tokens=2000, temperature=0.8)
    except Exception:
        return rows

    generated: dict[str, dict[str, Any]] = {}
    for line in response.splitlines():
        if not line.strip():
            continue
        parts = [segment.strip() for segment in line.split("|", 3)]
        if len(parts) < 4:
            continue
        key, title, body, label_hint = parts[:4]
        if key not in {row["id"] for row in rows}:
            continue
        generated[key] = {"title": title, "body": body, "label_hint": label_hint if label_hint and label_hint != "null" else None}

    updated: list[dict[str, Any]] = []
    for row in rows:
        if row["id"] in generated:
            item = dict(row)
            item["title"] = generated[row["id"]]["title"]
            item["body"] = generated[row["id"]]["body"]
            item["label_hint"] = generated[row["id"]]["label_hint"]
            updated.append(item)
        else:
            updated.append(row)
    return updated


def maybe_misspell(title: str, body: str, rng: random.Random) -> tuple[str, str]:
    misspell_target = rng.random() < 0.08
    if not misspell_target:
        return title, body
    replacements = {
        "battery": "battrry",
        "swelling": "swellling",
        "charge": "charege",
        "small": "smal",
        "great": "gr8",
        "quality": "qualtiy",
        "issues": "isssues",
        "arrived": "arrvied",
        "defect": "defct",
        "power": "pwoer",
    }
    def apply(text: str) -> str:
        for original, replacement in replacements.items():
            text = re.sub(rf"\b{re.escape(original)}\b", replacement, text, flags=re.IGNORECASE)
        return text
    return apply(title), apply(body)


def add_planted_review_variants(rows: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    for index, row in enumerate(rows[:25]):
        row["product_id"] = "P-014"
        row["supplier_id"] = "S-03"
        row["batch_id"] = "B-2026-07"
        row["title"] = "Battery swelling report"
        row["body"] = "Battery swelling on the P-014 power bank after charging. The battery on this unit swelled and the device became unsafe to use."
        row["label_hint"] = "manufacturing_defect"
        row["rating"] = 1 if index % 2 == 0 else 2

    for index, row in enumerate(rows[25:55]):
        row["product_id"] = "P-027"
        row["supplier_id"] = "S-04"
        row["batch_id"] = "B-2026-08"
        row["title"] = "Runs small"
        row["body"] = "This P-027 product runs small and the size does not fit comfortably even though I ordered the listed size."
        row["label_hint"] = "size_fit_issue"
        row["rating"] = 2 if index % 2 == 0 else 3

    for index, row in enumerate(rows[55:110]):
        row["product_id"] = "P-009"
        row["supplier_id"] = "S-02"
        row["batch_id"] = "B-2026-09"
        row["title"] = "Great battery life"
        row["body"] = "Great battery life on the P-009 earbuds and I love the sound, but it is a strong battery-life positive review with no defect."
        row["label_hint"] = None
        row["rating"] = 4 if index % 2 == 0 else 5

    # 5% distractors that mention the keywords but do not indicate a defect or fit problem.
    distractor_indices = set(rng.sample(range(len(rows)), max(1, len(rows) // 20)))
    for index in distractor_indices:
        if index >= len(rows):
            continue
        row = rows[index]
        if index % 2 == 0:
            row["title"] = "Battery life is great"
            row["body"] = "Battery life is great, and the device feels reliable; I do not have a complaint about the battery."
            row["label_hint"] = None
        else:
            row["title"] = "Runs small but I love the fit"
            row["body"] = "Runs small but I love the fit, and I still plan to keep it because the style works well for me."
            row["label_hint"] = None

    for index, row in enumerate(rows):
        if index % 12 == 0 and row.get("label_hint") is None:
            # add misspellings to a small share of positive and neutral reviews
            row["title"], row["body"] = maybe_misspell(row["title"], row["body"], rng)
    return rows


def add_planted_supplier_variants(rows: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    for index, row in enumerate(rows[:18]):
        row["product_id"] = "P-014"
        row["supplier_id"] = "S-03"
        row["batch_id"] = "B-2026-07"
        row["title"] = "Battery swelling in QA batch"
        row["body"] = "Supplier QA report: the P-014 battery pack showed battery swelling during charge testing and elevated heat in the latest batch B-2026-07."
        row["label_hint"] = "manufacturing_defect"

    for index, row in enumerate(rows[18:36]):
        row["product_id"] = "P-027"
        row["supplier_id"] = "S-04"
        row["batch_id"] = "B-2026-08"
        row["title"] = "Fit issue flagged"
        row["body"] = "Several apparel units from the P-027 order run small compared with the size chart and create a fit issue in the warehouse."
        row["label_hint"] = "size_fit_issue"

    distractor_indices = set(rng.sample(range(len(rows)), max(1, len(rows) // 20)))
    for index in distractor_indices:
        row = rows[index]
        if index % 2 == 0:
            row["title"] = "Battery life is great"
            row["body"] = "Battery life is great and the pack is performing well; no defect observed in this lot."
            row["label_hint"] = None
        else:
            row["title"] = "Runs small but I love the fit"
            row["body"] = "Runs small but I love the fit and the color; the design remains acceptable for the customer."
            row["label_hint"] = None
    return rows


def add_inventory_variants(rows: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    for index, row in enumerate(rows[:25]):
        row["product_id"] = "P-014"
        row["supplier_id"] = "S-03"
        row["batch_id"] = "B-2026-07"
        row["title"] = "Inventory batch alert"
        row["body"] = "Inventory check for batch B-2026-07 flagged unusual battery swelling and elevated heat in stored P-014 units."
        row["label_hint"] = "manufacturing_defect"
    for index, row in enumerate(rows[25:45]):
        row["product_id"] = "P-027"
        row["supplier_id"] = "S-04"
        row["batch_id"] = "B-2026-08"
        row["title"] = "Size-fit stock issue"
        row["body"] = "Warehouse inventory shows should-be size M P-027 units running small and creating excess size-fit returns."
        row["label_hint"] = "size_fit_issue"
    return rows


def build_review_rows(total: int, rng: random.Random) -> list[dict[str, Any]]:
    product_rows = load_products()
    products = [row["product_id"] for row in product_rows]
    generated: list[dict[str, Any]] = []
    for idx in range(total):
        product_id = rng.choice(products)
        if idx % 50 == 0:
            product_id = "P-014"
        elif idx % 60 == 0:
            product_id = "P-027"
        elif idx % 80 == 0:
            product_id = "P-009"
        supplier_id = next((row["supplier_id"] for row in product_rows if row["product_id"] == product_id), "S-01")
        row = {
            "id": f"rev-{idx + 1:05d}",
            "source_type": "review",
            "title": "Battery performance issue" if idx % 9 == 0 else "Customer comment",
            "body": "Battery performance is acceptable but the device feels warm during charging.",
            "product_id": product_id,
            "supplier_id": supplier_id,
            "batch_id": f"B-{idx % 12 + 1:02d}-2026",
            "date": (dataset_today() - __import__("datetime").timedelta(days=(idx % 30))).isoformat(),
            "rating": rng.randint(1, 5),
            "label_hint": None,
        }
        if idx % 7 == 0:
            row["title"] = "Battery swelling review"
            row["body"] = "The battery swelled and the phone became hot after charging; this is a serious battery defect."
            row["label_hint"] = "manufacturing_defect"
        elif idx % 11 == 0:
            row["title"] = "Runs small"
            row["body"] = "The item runs small and the fit is poor; I need a different size."
            row["label_hint"] = "size_fit_issue"
        elif idx % 13 == 0:
            row["title"] = "Battery life is great"
            row["body"] = "Battery life is great and the device works well for daily use; no complaint here."
            row["label_hint"] = None
        else:
            row["body"] = "Customer review: the product arrived and works as expected for everyday use."
        row["title"], row["body"] = maybe_misspell(row["title"], row["body"], rng)
        generated.append(row)
    generated = add_planted_review_variants(generated, rng)
    return generated


def build_supplier_rows(total: int, rng: random.Random) -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    for idx in range(total):
        product_id = "P-014" if idx % 18 == 0 else "P-027" if idx % 17 == 0 else "P-009"
        supplier_id = "S-03" if product_id == "P-014" else "S-04" if product_id == "P-027" else "S-02"
        batch_id = "B-2026-07" if product_id == "P-014" else "B-2026-08" if product_id == "P-027" else "B-2026-09"
        body = "QA note: product quality remains stable across the batch with no major defect reported."
        title = "Supplier QA note"
        label_hint = None
        if idx % 11 == 0:
            title = "Battery swelling QA note"
            body = "Supplier QA note: battery swelling was observed in the P-014 units and the batch B-2026-07 was quarantined."
            label_hint = "manufacturing_defect"
        elif idx % 7 == 0:
            title = "Runs small batch review"
            body = "Warehouse inspection: the P-027 items run small and the size tolerance is outside standard limits."
            label_hint = "size_fit_issue"
        elif idx % 13 == 0:
            title = "Battery life is great"
            body = "Battery life is great on the P-009 trial units and the defect rate remained low in this lot."
            label_hint = None
        row = {
            "id": f"sup-{idx + 1:05d}",
            "source_type": "supplier_record",
            "title": title,
            "body": body,
            "product_id": product_id,
            "supplier_id": supplier_id,
            "batch_id": batch_id,
            "date": (dataset_today() - __import__("datetime").timedelta(days=(idx % 45))).isoformat(),
            "label_hint": label_hint,
        }
        generated.append(row)
    generated = add_planted_supplier_variants(generated, rng)
    return generated


def build_inventory_rows(total: int, rng: random.Random) -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    for idx in range(total):
        product_id = "P-014" if idx % 10 == 0 else "P-027" if idx % 7 == 0 else "P-009"
        supplier_id = "S-03" if product_id == "P-014" else "S-04" if product_id == "P-027" else "S-02"
        batch_id = "B-2026-07" if product_id == "P-014" else "B-2026-08" if product_id == "P-027" else "B-2026-09"
        row = {
            "id": f"inv-{idx + 1:05d}",
            "source_type": "inventory",
            "title": "Inventory control note",
            "body": "Inventory count is normal and no stock anomaly is present for the current batch.",
            "product_id": product_id,
            "supplier_id": supplier_id,
            "batch_id": batch_id,
            "date": (dataset_today() - __import__("datetime").timedelta(days=(idx % 21))).isoformat(),
            "label_hint": None,
        }
        if idx % 18 == 0:
            row["title"] = "Battery swelling stock alert"
            row["body"] = "Battery swelling note from warehouse: P-014 units in batch B-2026-07 were isolated after heat and swelling checks."
            row["label_hint"] = "manufacturing_defect"
        elif idx % 12 == 0:
            row["title"] = "Runs small inventory signal"
            row["body"] = "Inventory signal: P-027 units run small across multiple sizes and need a fit audit."
            row["label_hint"] = "size_fit_issue"
        generated.append(row)
    generated = add_inventory_variants(generated, rng)
    return generated


def build_policy_rows(total: int) -> list[dict[str, Any]]:
    templates = [
        ("Return window", "Return window: products with battery swelling or manufacturer defects may be returned within 14 days of delivery.", "manufacturing_defect"),
        ("Battery defect rule", "Battery-related defects including swelling, overheating, and sudden battery drain are covered under the defect return policy.", "manufacturing_defect"),
        ("Fit issue rule", "Items that run small or do not match the size guide are eligible for exchange or refund within the standard fit window.", "size_fit_issue"),
        ("Non-returnable listing", "Non-returnable items: opened consumables and accessories are not eligible unless there is a documented defect or quality issue.", None),
        ("Electronics defect window", "Electronics with swelling, heat damage, or battery failure fall under the defect return policy and are reviewed within 48 hours.", "manufacturing_defect"),
        ("No remorse policy", "Change-of-mind returns are not accepted for opened electronics unless the item is materially different from the listing.", "not_as_described"),
        ("Packaging damage", "Damaged-in-transit items must be reported within 48 hours and supported by courier evidence before replacement is approved.", "damaged_in_transit"),
        ("Size guarantee", "Size-fit claims are treated as valid if the product is outside the stated size range or the listed size runs unusually small.", "size_fit_issue"),
    ]
    rows: list[dict[str, Any]] = []
    for idx in range(total):
        title, body, hint = templates[idx % len(templates)]
        rows.append({
            "id": f"pol-{idx + 1:03d}",
            "source_type": "policy",
            "title": title,
            "body": body,
            "product_id": None,
            "supplier_id": None,
            "batch_id": None,
            "date": dataset_today().isoformat(),
            "label_hint": hint,
        })
    return rows


def build_historical_rows() -> list[dict[str, Any]]:
    if not RETURNS_PATH.exists():
        return []
    with RETURNS_PATH.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append({
                "id": f"hist-{row.get('return_id', 'unknown') or 'row'}",
                "source_type": "historical_return",
                "title": "Historical return snippet",
                "body": (row.get("text") or "").strip(),
                "product_id": row.get("product_id"),
                "supplier_id": row.get("supplier_id"),
                "batch_id": row.get("batch_id"),
                "date": (row.get("return_date") or dataset_today().isoformat()),
                "label_hint": row.get("root_cause_label") or None,
            })
    return rows


def generate_corpus(seed: int = SEED) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    reviews = build_review_rows(5000, rng)
    suppliers = build_supplier_rows(300, rng)
    inventory = build_inventory_rows(200, rng)
    policy = build_policy_rows(15)
    historical = build_historical_rows()

    def apply_llm_batches(rows: list[dict[str, Any]], source_type: str) -> list[dict[str, Any]]:
        if not rows:
            return rows
        llm_count = max(1, int(len(rows) * 0.4))
        llm_indices = set(rng.sample(range(len(rows)), llm_count))
        llm_batch = [rows[index] for index in sorted(llm_indices)]
        if not llm_batch:
            return rows
        batches = [llm_batch[i:i + LLM_BATCH_SIZE] for i in range(0, len(llm_batch), LLM_BATCH_SIZE)]
        expanded: list[dict[str, Any]] = []
        for idx, row in enumerate(rows):
            if idx in llm_indices:
                expanded.append(row)
            else:
                expanded.append(row)
        for batch in batches:
            expanded_batch = _llm_expand_rows(batch, source_type, rng)
            for row in expanded_batch:
                position = next((i for i, candidate in enumerate(rows) if candidate["id"] == row["id"]), None)
                if position is not None:
                    expanded[position] = row
        return expanded

    reviews = apply_llm_batches(reviews, "review")
    suppliers = apply_llm_batches(suppliers, "supplier_record")
    inventory = apply_llm_batches(inventory, "inventory")

    records = reviews + suppliers + inventory + policy + historical
    for record in records:
        if record.get("label_hint") not in ROOT_CAUSES and record.get("label_hint") is not None:
            record["label_hint"] = None

    return records


def write_corpus(rows: list[dict[str, Any]], output_path: Path = OUTPUT_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in rows:
            payload = {k: v for k, v in record.items() if v is not None}
            if payload.get("source_type") != "review":
                payload.pop("rating", None)
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def generate_readme(counts: Counter[str]) -> None:
    file_text = (
        "# Corpus dataset\n\n"
        "This corpus is deterministic and seeded for retrieval evaluation. It combines synthetic reviews, supplier quality notes, inventory signals, policy passages, and exported historical returns.\n\n"
        "## Source counts\n\n"
        "| source_type | count |\n"
        "| --- | ---: |\n"
        f"| review | {counts.get('review', 0)} |\n"
        f"| supplier_record | {counts.get('supplier_record', 0)} |\n"
        f"| historical_return | {counts.get('historical_return', 0)} |\n"
        f"| inventory | {counts.get('inventory', 0)} |\n"
        f"| policy | {counts.get('policy', 0)} |\n\n"
        "## Planted patterns\n\n"
        "- P-014 / S-03 / batch B-2026-07 includes battery swelling defect text.\n"
        "- P-027 records include the phrase 'runs small' with size-fit labels.\n"
        "- P-009 review entries include keyword distractor text such as 'great battery life' while remaining neutral.\n"
        "- Historical returns come from Member 2's `data/returns/returns.csv`, retaining only text fields and excluding customer references.\n"
        "- Approximately 5% of passages use distractor wording that shares keywords but is semantically different.\n"
        "- Misspellings are intentionally injected into roughly 8% of review passages.\n"
    )
    README_PATH.write_text(file_text, encoding="utf-8")


if __name__ == "__main__":
    rows = generate_corpus()
    write_corpus(rows, OUTPUT_PATH)
    counts = Counter(row["source_type"] for row in rows)
    generate_readme(counts)
    print(f"Wrote {len(rows)} records to {OUTPUT_PATH}")
    print(dict(sorted(counts.items())))
