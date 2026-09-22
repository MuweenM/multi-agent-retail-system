# Agent Contracts (v1.1)

Current Contract Version: `1.1` (`shared/retail_common/__init__.py`)

All 4 agents communicate over **Model Context Protocol (MCP)** using Pydantic models defined in `shared/retail_common/schemas/`.

---

## MCP Tools & Schemas

| Agent | Tool Name | Parameters | Output Model | Description |
|---|---|---|---|---|
| **1 - Intake** | `extract_return_info` | `text: str`, `tenant_id: str = "demo"` | `IntakeOutput` | Extracts structured return info, entities, language, and redacts PII into `clean_text`. |
| **2 - Root Cause** | `analyze_root_cause` | `product: str`, `issue: str`, `tenant_id: str = "demo"` | `RootCauseOutput` | Performs root cause pattern analysis, classification, and emerging spike detection. |
| **3 - Retrieval** | `retrieve_evidence` | `query: str`, `top_k: int = 5`, `method: str = "hybrid"`, `tenant_id: str = "demo"` | `EvidenceOutput` | Retrieves supporting evidence from reviews, supplier notes, historical returns, or inventory. |
| **4 - Decision** | `generate_final_recommendation` | `return_text: str`, `tenant_id: str = "demo"` | `DecisionOutput` | Orchestrates agents 1-3, computes resolution decision, cites evidence, and produces audit trace. |

---

## Canonical Taxonomy (`shared/retail_common/taxonomy.py`)

All labels across all agents MUST be drawn from these tuples — never invent ad-hoc strings:

- **Root Causes (`ROOT_CAUSES`)**: `manufacturing_defect`, `damaged_in_transit`, `wrong_item_shipped`, `size_fit_issue`, `not_as_described`, `quality_durability`, `late_delivery`, `change_of_mind`, `policy_abuse_suspected`, `unknown`
- **Intents (`INTENTS`)**: `return`, `exchange`, `refund`, `complaint`, `unknown`
- **Sentiments (`SENTIMENTS`)**: `positive`, `neutral`, `negative`
- **Decisions (`DECISIONS`)**: `approve`, `reject`, `escalate`, `request_info`
- **Source Types (`SOURCE_TYPES`)**: `review`, `supplier_record`, `historical_return`, `inventory`, `policy`

---

## Bulk Analytics Models (`shared/retail_common/schemas/bulk.py`)

Used by Agent 4's batch/bulk intelligence engine and frontend dashboard:
- `BulkRow`: Single incoming return row in a CSV/batch upload.
- `RowError`: Error detail encountered during row processing.
- `BulkJob`: Job progress tracker (`queued`, `running`, `done`, `failed`).
- `Finding`: Statistically backed insight (anomaly spike, supplier defect concentration, p-value).
- `IssueCluster`: Unsupervised cluster of returns with top keywords and dominant root cause.
- `BulkSummary`: Overall batch return resolution summary and executive report.
- `ProductRootCauseReport`: Product-level root-cause breakdown, weekly trend, and recommendations.

---

## Changed in v1.1

Data Contract v1.1 is strictly **additive** and **100% backward compatible** with v1.0 payloads. All newly added fields provide safe default values.

### Summary of Additions

1. **`shared/retail_common/taxonomy.py` [NEW]**:
   - Canonical enumerations for root causes, intents, sentiments, decisions, and source types.

2. **`IntakeOutput` (`schemas/intake.py`)**:
   - `return_id: str = ""`
   - `tenant_id: str = "demo"`
   - `clean_text: str = ""` (sanitised, spell-corrected, PII-redacted text)
   - `summary: str = ""` (concise <=20 word summary)
   - `product_id: str | None = None`
   - `product_match_score: float = 0.0`
   - `entities: list[Entity] = []` (extracted entities with type, text, start, end)
   - `lang: str = "en"` (`en`, `si`, `si-rom`)
   - `pii_types_found: list[str] = []` (redacted PII categories)
   - `flags: list[str] = []` (`injection_suspected`, `spelling_corrected`, `llm_fallback`, `translated`)

3. **`RootCauseOutput` & `RootCauseCandidate` (`schemas/rootcause.py`)**:
   - `RootCauseCandidate.top_terms: list[str] = []` (words driving the classification score)
   - `RootCauseOutput.product_id: str | None = None`
   - `RootCauseOutput.supplier_id: str | None = None`
   - `RootCauseOutput.model_name: str = ""` (e.g. `tfidf_logreg_v3`, `llm_fallback`)
   - `RootCauseOutput.model_version: str = ""`
   - `RootCauseOutput.is_emerging_spike: bool = False`
   - `RootCauseOutput.abuse_risk: float = 0.0` (0..1 score)
   - `RootCauseOutput.notes: list[str] = []`

4. **`EvidenceOutput` & `EvidenceItem` (`schemas/evidence.py`)**:
   - `EvidenceItem.title: str = ""`
   - `EvidenceItem.method: str = ""` (`tfidf`, `bm25`, `dense`, `hybrid`)
   - `EvidenceItem.matched_terms: list[str] = []`
   - `EvidenceItem.zone: str = ""` (`title`, `body`, `supplier_notes`)
   - `EvidenceItem.label_hint: str | None = None`
   - `EvidenceItem.metadata: dict[str, str] = {}`
   - `EvidenceOutput.corrected_query: str = ""`
   - `EvidenceOutput.expanded_terms: list[str] = []`
   - `EvidenceOutput.method: str = "hybrid"`
   - `EvidenceOutput.latency_ms: int = 0`

5. **`DecisionOutput` & `AgentStep` (`schemas/decision.py`)**:
   - `AgentStep`: Structure representing orchestrator execution steps (`agent`, `tool`, `ok`, `latency_ms`, `note`).
   - `DecisionOutput.return_id: str = ""`
   - `DecisionOutput.decision: str = "escalate"` (`approve`, `reject`, `escalate`, `request_info`)
   - `DecisionOutput.citations: list[str] = []` (source IDs cited)
   - `DecisionOutput.reasoning_steps: list[str] = []` (plain-English audit log)
   - `DecisionOutput.human_review_reasons: list[str] = []`
   - `DecisionOutput.risk_flags: list[str] = []`
   - `DecisionOutput.agent_trace: list[AgentStep] = []`
   - `DecisionOutput.evidence_support: float = 0.0`
   - `DecisionOutput.disclaimer: str = "AI suggestion. A person must confirm before any action."`

6. **`shared/retail_common/schemas/bulk.py` [NEW]**:
   - Batch and bulk analytics models supporting aggregated reporting and intelligence features.

7. **Contract Version Constant**:
   - `retail_common.CONTRACT_VERSION = "1.1"` in `shared/retail_common/__init__.py`.
