"""Generate the deterministic Phase 2 labelled returns dataset."""

from __future__ import annotations

import csv
import os
import random
import re
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from retail_common.taxonomy import ROOT_CAUSES


SEED = 3041
TARGET_ROWS = 4000
LLM_BATCH_SIZE = 20
DATASET_TODAY_DEFAULT = date(2026, 9, 22)
OUTPUT_PATH = Path(__file__).with_name("returns.csv")
PRODUCTS_PATH = Path(__file__).parents[1] / "catalog" / "products.csv"

FIELDNAMES = [
    "return_id", "order_id", "product_id", "supplier_id", "batch_id",
    "courier", "store_id", "customer_ref", "text", "root_cause_label",
    "order_value_lkr", "purchase_date", "return_date", "channel", "district",
]

LABEL_TARGETS = {
    "manufacturing_defect": 0.22,
    "damaged_in_transit": 0.15,
    "wrong_item_shipped": 0.10,
    "size_fit_issue": 0.16,
    "not_as_described": 0.12,
    "quality_durability": 0.10,
    "late_delivery": 0.05,
    "change_of_mind": 0.05,
    "policy_abuse_suspected": 0.04,
    "unknown": 0.01,
}

TEMPLATES = {
    "manufacturing_defect": [
        "The {product} stopped working after a few days.",
        "There is a clear defect in the {product}; it arrived faulty.",
        "The {product} has a manufacturing problem and will not work properly.",
    ],
    "damaged_in_transit": [
        "The {product} arrived damaged and the box was crushed.",
        "Courier handling damaged the {product} during delivery.",
        "The package was dented and the {product} was broken on arrival.",
    ],
    "wrong_item_shipped": [
        "I received the wrong item instead of the {product}.",
        "The parcel contains a different model, not the {product} I ordered.",
        "Wrong product was fulfilled for this order.",
    ],
    "size_fit_issue": [
        "The {product} runs small and does not fit.",
        "The size of the {product} is too tight for me.",
        "The {product} is not the right fit, so I need another size.",
    ],
    "not_as_described": [
        "The {product} is not as described in the listing.",
        "The item does not match what was advertised online.",
        "The {product} differs from the product description.",
    ],
    "quality_durability": [
        "The {product} feels flimsy and the material is poor quality.",
        "The {product} did not hold up after normal use.",
        "The stitching and material quality of the {product} are disappointing.",
    ],
    "late_delivery": [
        "The {product} arrived late and I no longer needed it.",
        "Delivery of the {product} was delayed beyond the promised date.",
        "The courier delivered the {product} too late.",
    ],
    "change_of_mind": [
        "I changed my mind about the {product} and want to return it.",
        "The {product} is fine but I prefer a different option.",
        "I no longer want the {product}; please process a return.",
    ],
    "policy_abuse_suspected": [
        "I am returning this high value {product} again.",
        "Please arrange another return for the {product}.",
        "This is a repeat return of the {product}.",
    ],
    "unknown": [
        "I need help with returning this item.",
        "There is an issue with my order but I cannot describe it clearly.",
    ],
}

DISTRICTS = ["Colombo", "Kandy", "Galle", "Jaffna", "Kurunegala", "Matara", "Negombo"]
COURIERS = ["C-1", "C-2", "C-3", "C-4"]
STORES = ["ST-01", "ST-02", "ST-03", "ST-04", "ST-05"]
CHANNELS = ["web", "mobile", "store", "marketplace"]
SUPPLIERS = [f"S-{number:02d}" for number in range(1, 9)]
HIGH_VALUE_PRODUCTS = ["P-011", "P-012", "P-014"]


def _dataset_today() -> date:
    value = os.getenv("DATASET_TODAY", "")
    if not value:
        env_path = Path(__file__).parents[2] / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("DATASET_TODAY="):
                    value = line.split("=", 1)[1].strip()
                    break
    return datetime.strptime(value or DATASET_TODAY_DEFAULT.isoformat(), "%Y-%m-%d").date()


def _load_products() -> list[dict[str, str]]:
    with PRODUCTS_PATH.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _noise(text: str, rng: random.Random, index: int) -> str:
    if index % 11 == 0:
        text = text.upper()
    elif index % 7 == 0:
        text = text.replace("the", "teh", 1)
    elif index % 13 == 0:
        text = text.replace("please", "plz", 1)
    if index % 17 == 0:
        text += " pls help"
    if index % 19 == 0:
        text += " mata return karanna"
    return text


def _template_text(label: str, product_name: str, rng: random.Random, index: int) -> str:
    return _noise(rng.choice(TEMPLATES[label]).format(product=product_name), rng, index)


def _llm_text_batch(rows: list[dict[str, str]], rng: random.Random) -> None:
    """Use the shared LLM mechanism in batches; preserve generation offline if unavailable."""
    try:
        from retail_common.llm_client import call_llm
    except Exception:
        return

    prompt_rows = "\n".join(
        f"{row['return_id']}: product={row['product_id']}, label={row['root_cause_label']}"
        for row in rows
    )
    prompt = (
        "Generate one short English retail return sentence per line for these labelled rows. "
        "Keep the meaning of each label, add realistic customer wording, and return only "
        "ID: sentence lines.\n" + prompt_rows
    )
    try:
        # The shared wrapper owns provider/API details; this call is intentionally batched at 20.
        response = call_llm(
            prompt,
            system="You generate synthetic English retail return text.",
            max_tokens=1600,
            temperature=0.9,
        )
        generated = {}
        for line in response.splitlines():
            match = re.match(r"\s*(RET-\d+)\s*:\s*(.+)", line)
            if match:
                generated[match.group(1)] = match.group(2).strip()
        for row in rows:
            if generated.get(row["return_id"]):
                row["text"] = generated[row["return_id"]]
    except Exception:
        # Missing credentials or an unavailable provider must not make the dataset non-reproducible.
        return


def _make_row(index: int, label: str, product: dict[str, str], today: date, rng: random.Random) -> dict[str, str]:
    return_date = today - timedelta(days=rng.randint(0, 179))
    purchase_date = return_date - timedelta(days=rng.randint(3, 30))
    supplier_id = product["supplier_id"]
    batch_id = f"B-{return_date.year}-{return_date.month:02d}"
    return {
        "return_id": f"RET-{index:05d}",
        "order_id": f"ORD-{index:06d}",
        "product_id": product["product_id"],
        "supplier_id": supplier_id,
        "batch_id": batch_id,
        "courier": rng.choice(COURIERS),
        "store_id": rng.choice(STORES),
        "customer_ref": f"cust-{rng.randint(1000, 9999):04d}",
        "text": _template_text(label, product["name"], rng, index),
        "root_cause_label": label,
        "order_value_lkr": product["price_lkr"],
        "purchase_date": purchase_date.isoformat(),
        "return_date": return_date.isoformat(),
        "channel": rng.choice(CHANNELS),
        "district": rng.choice(DISTRICTS),
    }


def _plant_patterns(rows: list[dict[str, str]], products: dict[str, dict[str, str]], today: date, rng: random.Random) -> None:
    """Apply the five planted evaluation stories after broad sampling."""
    p014 = products["P-014"]
    for offset in range(21):
        row = rows[offset]
        day = today - timedelta(days=offset)
        row.update(product_id="P-014", supplier_id="S-03", batch_id="B-2026-07", courier="C-1",
                   root_cause_label="manufacturing_defect", text=f"Battery swelling on the {p014['name']} after charging.",
                   order_value_lkr=p014["price_lkr"], purchase_date=(day - timedelta(days=10)).isoformat(), return_date=day.isoformat())

    p027 = products["P-027"]
    for offset, row in enumerate(rows[21:61]):
        day = today - timedelta(days=offset + 1)
        row.update(product_id="P-027", supplier_id=SUPPLIERS[offset % len(SUPPLIERS)], batch_id=f"B-P027-{offset + 1:02d}",
                   root_cause_label="size_fit_issue", text="This shirt runs small even though the listed size is correct.",
                   order_value_lkr=p027["price_lkr"], purchase_date=(day - timedelta(days=12)).isoformat(), return_date=day.isoformat())

    electronics = [product for product in products.values() if product["category"] == "electronics"]
    for offset, row in enumerate(rows[61:101]):
        product = electronics[offset % len(electronics)]
        day = today - timedelta(days=offset % 7)
        row.update(product_id=product["product_id"], supplier_id=product["supplier_id"], courier="C-2",
                   root_cause_label="damaged_in_transit", text=f"The {product['name']} arrived damaged after courier delivery.",
                   order_value_lkr=product["price_lkr"], purchase_date=(day - timedelta(days=8)).isoformat(), return_date=day.isoformat())

    high_value = [product for product in products.values() if product["product_id"] in HIGH_VALUE_PRODUCTS]
    for customer_number in range(12):
        customer = f"cust-repeat-{customer_number + 1:02d}"
        for repeat in range(6):
            row = rows[101 + customer_number * 6 + repeat]
            product = high_value[(customer_number + repeat) % len(high_value)]
            day = today - timedelta(days=(customer_number * 4 + repeat) % 60)
            row.update(customer_ref=customer, product_id=product["product_id"], supplier_id=product["supplier_id"],
                       root_cause_label="change_of_mind", text=f"I changed my mind about the {product['name']} and want a return.",
                       order_value_lkr=product["price_lkr"], purchase_date=(day - timedelta(days=10)).isoformat(), return_date=day.isoformat())

    p009 = products["P-009"]
    for row in rows[173:223]:
        row.update(product_id="P-009", supplier_id="S-02", root_cause_label="not_as_described",
                   text="Great battery life, but the listing claimed noise cancelling and this product does not have it.",
                   order_value_lkr=p009["price_lkr"])


def generate(output_path: Path = OUTPUT_PATH, seed: int = SEED, target_rows: int = TARGET_ROWS) -> list[dict[str, str]]:
    if not set(LABEL_TARGETS).issubset(ROOT_CAUSES):
        raise ValueError("label targets must use shared ROOT_CAUSES")
    rng = random.Random(seed)
    today = _dataset_today()
    product_rows = _load_products()
    products = {row["product_id"]: row for row in product_rows}
    labels = [label for label, fraction in LABEL_TARGETS.items() for _ in range(round(target_rows * fraction))]
    labels.extend(["unknown"] * (target_rows - len(labels)))
    rng.shuffle(labels)
    rows = [_make_row(index + 1, label, rng.choice(product_rows), today, rng) for index, label in enumerate(labels)]
    _plant_patterns(rows, products, today, rng)

    # District is descriptive metadata only and must never be used as a model feature.
    # Keep the protected planted examples deterministic; use the LLM path for 30% of all rows.
    llm_rows = rows[223:223 + round(target_rows * 0.30)]
    for start in range(0, len(llm_rows), LLM_BATCH_SIZE):
        _llm_text_batch(llm_rows[start:start + LLM_BATCH_SIZE], rng)

    noise_count = max(1, round(target_rows * 0.05))
    noise_indices = rng.sample(range(223, target_rows), noise_count)
    for index in noise_indices:
        current = rows[index]["root_cause_label"]
        alternatives = [label for label in ROOT_CAUSES if label != current]
        rows[index]["root_cause_label"] = rng.choice(alternatives)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    generated_rows = generate()
    print(f"Wrote {len(generated_rows)} rows to {OUTPUT_PATH}")
    print(dict(Counter(row["root_cause_label"] for row in generated_rows)))