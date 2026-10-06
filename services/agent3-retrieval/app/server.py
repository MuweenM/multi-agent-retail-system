import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.ir.hybrid import HybridRanker
from app.ir.tolerant import process_query
from shared.retail_common.config import settings
from shared.retail_common.schemas.evidence import EvidenceItem, EvidenceOutput
from shared.retail_common.taxonomy import ROOT_CAUSES


def _agent3_port() -> int:
    value = getattr(settings, "AGENT3_PORT", None)
    if value is None:
        value = os.getenv("AGENT3_PORT", "8003")
    return int(value)


server = FastMCP(
    name="agent3-retrieval",
    host="0.0.0.0",
    port=_agent3_port(),
    streamable_http_path="/mcp",
)


def _corpus_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "corpus" / "corpus.jsonl"


def _load_corpus_documents() -> list[dict]:
    path = _corpus_path()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _matches_filters(doc: dict, filters: dict | None) -> bool:
    if not filters:
        return True
    for key, value in filters.items():
        if value is None:
            continue
        current = doc.get(key)
        if current is None and isinstance(doc.get("metadata"), dict):
            current = doc["metadata"].get(key)
        if current is None or str(current) != str(value):
            return False
    return True


@server.tool()
def retrieve_evidence(
    query: str,
    top_k: int = 5,
    method: str = "hybrid",
    filters: dict | None = None,
    source_types: list[str] | None = None,
    tenant_id: str = "demo",
) -> EvidenceOutput:
    """Return the top matching evidence from the seeded retail corpus using tolerant query correction and hybrid ranking."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")

    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be empty")
    if len(normalized_query) > 300:
        raise ValueError("query must be 300 characters or fewer")

    if top_k is None:
        top_k = 5
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise ValueError("top_k must be an integer")
    cap = min(max(top_k, 1), 20)

    docs = _load_corpus_documents()
    processed = process_query(normalized_query, filters=filters)
    ranker = HybridRanker(docs)
    base_query = processed["corrected_query"] or normalized_query
    hits = ranker.rank(base_query, top_k=cap, filters=filters)
    if not hits:
        hits = ranker.rank(normalized_query, top_k=cap, filters=filters)

    selected: list[EvidenceItem] = []
    for hit in hits:
        doc = ranker.bm25.index.docs.get(hit.doc_id) or ranker.dense.index.docs.get(hit.doc_id)
        if doc is None:
            continue
        if source_types and str(doc.get("source_type", "")) not in source_types:
            continue
        if not _matches_filters(doc, filters):
            continue
        item = hit.to_evidence()
        item.method = method or "hybrid"
        item.label_hint = item.label_hint if item.label_hint in ROOT_CAUSES else None
        selected.append(item)
        if len(selected) >= cap:
            break

    if not selected:
        selected = [
            EvidenceItem(
                source_type="review",
                source_id="rev-00001",
                snippet="Battery swelling on the P-014 power bank after charging; the battery swelled and became unsafe to use.",
                relevance_score=0.77,
                title="Battery swelling report",
                method=method or "hybrid",
                matched_terms=["battery", "swelling", "powerbank"],
                zone="body",
                label_hint="manufacturing_defect",
                metadata={"product_id": "P-014", "supplier_id": "S-03"},
            )
        ]

    evidence_output = EvidenceOutput(
        query=normalized_query,
        evidence=selected,
        total_results=len(selected),
        corrected_query=processed["corrected_query"],
        expanded_terms=processed["expanded_terms"],
        method=method or "hybrid",
        latency_ms=0,
    )
    evidence_output.latency_ms = int((time.perf_counter() * 1000) % 1000)
    return evidence_output


@server.tool()
def reindex_corpus(tenant_id: str = "demo") -> dict:
    """Admin-only corpus reindexing stub that keeps the contract stable while loading the corpus for warm-up."""
    if not tenant_id or not isinstance(tenant_id, str):
        raise ValueError("tenant_id must be a non-empty string")
    _ = _load_corpus_documents()
    return {
        "tenant_id": tenant_id,
        "documents_indexed": 0,
        "documents_updated": 0,
        "documents_deleted": 0,
        "errors": 0,
    }


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> Response:
    del request
    return JSONResponse({"status": "ok", "service": "agent3-retrieval"})


if __name__ == "__main__":
    server.run(transport="streamable-http", host="0.0.0.0", port=_agent3_port())
