# Agent Contracts

Current Contract Version: **v1.1** (`CONTRACT_VERSION = "1.1"`)

All inter-agent communication and output contracts are strictly typed using Pydantic models defined in `shared/retail_common/schemas/`. Standard vocabulary across all agents is maintained in `shared/retail_common/taxonomy.py`.

## Core MCP Tools & Output Schemas

| Agent | Tool name | Input | Output schema | Key Output Fields |
|---|---|---|---|---|
| 1 - Intake | `extract_return_info` | `text: str`, `tenant_id: str = "demo"` | `IntakeOutput` | `raw_text`, `product`, `issue`, `intent`, `sentiment`, `confidence`, `clean_text`, `summary`, `product_id`, `product_match_score`, `entities`, `lang`, `pii_types_found`, `flags` |
| 2 - Root Cause | `analyze_root_cause` | `product: str, issue: str` | `RootCauseOutput` | `product`, `issue`, `candidates`, `top_candidate`, `confidence`, `product_id`, `supplier_id`, `model_name`, `model_version`, `is_emerging_spike`, `abuse_risk`, `notes` |
| 3 - Retrieval | `retrieve_evidence` | `query: str, top_k: int = 5, method: str = "hybrid"` | `EvidenceOutput` | `query`, `evidence`, `total_results`, `corrected_query`, `expanded_terms`, `method`, `latency_ms` |
| 4 - Decision | `generate_final_recommendation` | `return_text: str` | `DecisionOutput` | `root_cause`, `confidence`, `evidence_summary`, `recommendation`, `requires_human_review`, `return_id`, `decision`, `citations`, `reasoning_steps`, `human_review_reasons`, `risk_flags`, `agent_trace`, `evidence_support`, `disclaimer` |

## Bulk Processing Schemas (`shared/retail_common/schemas/bulk.py`)

- `BulkRow`: Single return item input row with optional metadata (`order_id`, `product_id`, `order_value_lkr`, etc.).
- `RowError`: Structured error reporting for malformed bulk ingestion rows.
- `BulkJob`: Job status tracking (`queued`, `running`, `done`, `failed`).
- `Finding`: Root cause, supplier concentration, or batch issue anomaly finding.
- `IssueCluster`: Grouping of related return issues with dominant root cause and top terms.
- `BulkSummary`: Aggregate return analytics across a batch or job.
- `ProductRootCauseReport`: Detailed historical return breakdown and supplier attribution per product.

## Taxonomy Reference (`shared/retail_common/taxonomy.py`)

- **Root Causes**: `manufacturing_defect`, `damaged_in_transit`, `wrong_item_shipped`, `size_fit_issue`, `not_as_described`, `quality_durability`, `late_delivery`, `change_of_mind`, `policy_abuse_suspected`, `unknown`
- **Intents**: `return`, `exchange`, `refund`, `complaint`, `unknown`
- **Sentiments**: `positive`, `neutral`, `negative`
- **Decisions**: `approve`, `reject`, `escalate`, `request_info`
- **Source Types**: `review`, `supplier_record`, `historical_return`, `inventory`, `policy`

---

## Changed in v1.1 (Additive)

Contract v1.1 is fully backwards compatible with v1.0. All v1.0 fields remain unchanged; all new fields supply sensible defaults so existing v1.0 JSON payloads continue to validate without errors:

1. **`shared/retail_common/__init__.py`**:
   - Introduced `CONTRACT_VERSION = "1.1"`.
2. **`shared/retail_common/taxonomy.py`**:
   - Added standard tuples for `ROOT_CAUSES`, `INTENTS`, `SENTIMENTS`, `DECISIONS`, and `SOURCE_TYPES`.
3. **`IntakeOutput` (`schemas/intake.py`)**:
   - Added `Entity` model (`type`, `text`, `start`, `end`).
   - Added `return_id`, `tenant_id`, `clean_text` (redacted text for LLM/downstream use), `summary`, `product_id`, `product_match_score`, `entities`, `lang`, `pii_types_found`, and `flags`.
4. **`RootCauseOutput` (`schemas/rootcause.py`)**:
   - Added `top_terms` to `RootCauseCandidate`.
   - Added `product_id`, `supplier_id`, `model_name`, `model_version`, `is_emerging_spike`, `abuse_risk`, and `notes`.
5. **`EvidenceOutput` (`schemas/evidence.py`)**:
   - Extended `EvidenceItem` with `title`, `method`, `matched_terms`, `zone`, `label_hint`, and `metadata`.
   - Added `corrected_query`, `expanded_terms`, `method`, and `latency_ms`.
6. **`DecisionOutput` (`schemas/decision.py`)**:
   - Added `AgentStep` model (`agent`, `tool`, `ok`, `latency_ms`, `note`).
   - Added `return_id`, `decision`, `citations`, `reasoning_steps`, `human_review_reasons`, `risk_flags`, `agent_trace`, `evidence_support`, and `disclaimer`.
7. **`schemas/bulk.py`**:
   - Introduced models for bulk uploads, job tracking, issue clustering, and supplier root cause analysis.
