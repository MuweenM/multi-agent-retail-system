"""CSV Bulk I/O and validation utility (Contract v1.1)."""

import csv
import hashlib
import hmac
import io
import os
from typing import List, Tuple
from retail_common.schemas.bulk import BulkRow, RowError

MAX_ROWS = 5000
MAX_TEXT_LEN = 2000

COLUMN_ALIASES = {
    "complaint": "text",
    "complaint_text": "text",
    "message": "text",
    "feedback": "text",
    "issue_description": "text",
    "return_reason": "text",
    "order": "order_id",
    "order_number": "order_id",
    "product": "product_id",
    "sku": "product_id",
    "customer": "customer_ref",
    "customer_id": "customer_ref",
    "value": "order_value_lkr",
    "price": "order_value_lkr",
    "amount": "order_value_lkr",
}


def sanitize_csv_cell(value: str) -> str:
    """Neutralize potential CSV formula injection (=, +, -, @)."""
    if not value:
        return value
    str_val = str(value)
    if str_val.startswith(("=", "+", "-", "@")):
        return "'" + str_val
    return str_val


def pseudonymize_customer(customer_ref: str | None, key: str | None = None) -> str | None:
    """Produce deterministic HMAC-SHA256 pseudonym for customer reference."""
    if not customer_ref:
        return None
    secret_key = key or os.getenv("PSEUDONYM_KEY", "default-dev-secret-key-12345")
    h = hmac.new(secret_key.encode("utf-8"), customer_ref.strip().encode("utf-8"), hashlib.sha256)
    return f"CUST-{h.hexdigest()[:12].upper()}"


def load_and_validate_csv(
    csv_content: str | bytes,
) -> Tuple[List[BulkRow], List[RowError]]:
    """Parse CSV content into validated BulkRow list and list of RowError."""
    if isinstance(csv_content, bytes):
        try:
            csv_str = csv_content.decode("utf-8")
        except UnicodeDecodeError:
            return [], [RowError(row=0, field="file", reason="Encoding must be valid UTF-8")]
    else:
        csv_str = csv_content

    reader = csv.DictReader(io.StringIO(csv_str))
    if not reader.fieldnames:
        return [], [RowError(row=0, field="header", reason="CSV has empty or missing header")]

    # Normalize column names with aliases
    normalized_headers = {}
    for h in reader.fieldnames:
        cleaned_h = h.strip().lower().replace(" ", "_")
        target_field = COLUMN_ALIASES.get(cleaned_h, cleaned_h)
        normalized_headers[h] = target_field

    if "text" not in normalized_headers.values():
        return [], [
            RowError(
                row=0,
                field="text",
                reason="Required column 'text' (or alias: complaint, message) missing in CSV",
            )
        ]

    valid_rows: List[BulkRow] = []
    errors: List[RowError] = []

    for idx, raw_row in enumerate(reader, start=1):
        if idx > MAX_ROWS:
            errors.append(
                RowError(
                    row=idx,
                    field="file",
                    reason=f"Exceeded maximum row limit of {MAX_ROWS} rows",
                )
            )
            break

        # Map to standard row dict
        mapped = {}
        for orig_key, val in raw_row.items():
            if val is not None:
                norm_key = normalized_headers.get(orig_key, orig_key)
                mapped[norm_key] = sanitize_csv_cell(val.strip())

        text = mapped.get("text", "").strip()

        # Validate required text
        if not text:
            errors.append(RowError(row=idx, field="text", reason="Return text is empty"))
            continue

        if len(text) > MAX_TEXT_LEN:
            errors.append(
                RowError(
                    row=idx,
                    field="text",
                    reason=f"Text exceeds {MAX_TEXT_LEN} character limit ({len(text)} chars)",
                )
            )
            continue

        # Parse order value if present
        order_val_lkr = None
        raw_val = mapped.get("order_value_lkr")
        if raw_val:
            try:
                # Remove currency symbols or commas if present
                cleaned_val = raw_val.replace("LKR", "").replace("Rs.", "").replace(",", "").strip()
                order_val_lkr = float(cleaned_val)
            except ValueError:
                errors.append(
                    RowError(
                        row=idx,
                        field="order_value_lkr",
                        reason=f"Invalid numeric value '{raw_val}'",
                    )
                )

        # Pseudonymize customer reference
        cust_ref = pseudonymize_customer(mapped.get("customer_ref"))

        row_obj = BulkRow(
            return_id=mapped.get("return_id", f"RET-{idx:05d}"),
            text=text,
            order_id=mapped.get("order_id"),
            product_id=mapped.get("product_id"),
            customer_ref=cust_ref,
            order_value_lkr=order_val_lkr,
            purchase_date=mapped.get("purchase_date"),
            return_date=mapped.get("return_date"),
            store_id=mapped.get("store_id"),
            courier=mapped.get("courier"),
        )
        valid_rows.append(row_obj)

    return valid_rows, errors
