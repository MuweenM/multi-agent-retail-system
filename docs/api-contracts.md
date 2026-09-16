# Agent Contracts

TODO: keep this table updated as you finalize each schema in shared/retail_common/schemas/

| Agent | Tool name | Input | Output schema |
|---|---|---|---|
| 1 - Intake | `extract_return_info` | `text: str` | `IntakeOutput` |
| 2 - Root Cause | `analyze_root_cause` | `product: str, issue: str` | `RootCauseOutput` |
| 3 - Retrieval | `retrieve_evidence` | `query: str, top_k: int, method: str` | `EvidenceOutput` |
| 4 - Decision | `generate_final_recommendation` | `return_text: str` | `DecisionOutput` |

Any change to a schema must be agreed with the team first — other agents depend on it.
