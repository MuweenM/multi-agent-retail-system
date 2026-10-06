"""Batch return info extraction with async concurrency and row-level fault tolerance."""

import asyncio
import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from retail_common.schemas.bulk import BulkRow, RowError
from retail_common.schemas.intake import IntakeOutput
from retail_common.bulk_io import pseudonymize_customer
from app.nlp.pipeline import process_intake_pipeline

CONCURRENCY_LIMIT = 8


async def _process_single_row(
    semaphore: asyncio.Semaphore,
    row: BulkRow,
    idx: int,
    tenant_id: str,
) -> tuple[int, IntakeOutput | None, RowError | None]:
    """Process single row under semaphore concurrency."""
    async with semaphore:
        try:
            if not row.text or not row.text.strip():
                return idx, None, RowError(row=idx, field="text", reason="Text is empty")

            if len(row.text) > 2000:
                return idx, None, RowError(row=idx, field="text", reason="Text exceeds 2000 character limit")

            # Pseudonymize customer reference if present
            pseudonymized_ref = pseudonymize_customer(row.customer_ref)

            # Process through NLP pipeline
            out = process_intake_pipeline(text=row.text, tenant_id=tenant_id)
            out.return_id = row.return_id or f"RET-{idx:05d}"
            
            # If explicit product_id given in row, match it
            if row.product_id:
                out.product_id = row.product_id

            return idx, out, None
        except Exception as e:
            return idx, None, RowError(row=idx, field="pipeline", reason=str(e))


async def process_intake_batch(
    rows: List[BulkRow],
    tenant_id: str = "demo",
) -> Dict[str, Any]:
    """Process batch of rows concurrently with Semaphore(8)."""
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    tasks = [
        _process_single_row(semaphore, row, idx, tenant_id)
        for idx, row in enumerate(rows, start=1)
    ]

    results_and_errors = await asyncio.gather(*tasks)

    results: List[IntakeOutput] = []
    errors: List[RowError] = []

    for _, res, err in sorted(results_and_errors, key=lambda x: x[0]):
        if res:
            results.append(res)
        if err:
            errors.append(err)

    return {
        "results": [r.model_dump() for r in results],
        "errors": [e.model_dump() for e in errors],
    }


def process_intake_batch_sync(
    rows: List[BulkRow],
    tenant_id: str = "demo",
) -> Dict[str, Any]:
    """Synchronous entry point for MCP tool."""
    return asyncio.run(process_intake_batch(rows=rows, tenant_id=tenant_id))
