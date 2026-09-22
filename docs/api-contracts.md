# Agent Contracts

TODO: keep this table updated as you finalize each schema in shared/retail_common/schemas/

| Agent          | Tool name                       | Input                                 | Output schema     |
| -------------- | ------------------------------- | ------------------------------------- | ----------------- |
| 1 - Intake     | `extract_return_info`           | `text: str`                           | `IntakeOutput`    |
| 2 - Root Cause | `analyze_root_cause`            | `product: str, issue: str`            | `RootCauseOutput` |
| 3 - Retrieval  | `retrieve_evidence`             | `query: str, top_k: int, method: str` | `EvidenceOutput`  |
| 4 - Decision   | `generate_final_recommendation` | `return_text: str`                    | `DecisionOutput`  |

## Agent 2 - Root Cause

### MCP tool

- **Name:** `analyze_root_cause`
- **Inputs:** `product: str`, `issue: str`
- **Output:** `RootCauseOutput`

`RootCauseOutput` contains:

- `product: str`
- `issue: str`
- `candidates: list[RootCauseCandidate]`
- `top_candidate: str`
- `confidence: float`

Each `RootCauseCandidate` contains `label: str`, `score: float`, and
`supporting_return_count: int`.

Supported root-cause labels are:

- `manufacturing defect`
- `shipping or packaging damage`
- `wrong item fulfilled`
- `size or fit issue`
- `quality or material issue`
- `missing parts or accessories`
- `customer preference`
- `unknown`

### Behavior

Agent 2 is deterministic and rule-based. It normalizes the product and issue
text, combines them, and scores each supported label by matching its configured
keywords. The highest-scoring label is returned as `top_candidate`, with scores
and confidence bounded from `0.0` to `1.0`. The public tool rejects empty or
whitespace-only `product` and `issue` values with `ValueError`.

When no configured rule matches, the tool returns `top_candidate: "unknown"`
with `confidence: 0.0`.

### Local service

- **Endpoint:** `http://localhost:8002/mcp`
- **Transport:** Streamable HTTP
- **Port:** `8002`
- **Startup:** from `services/agent2-rootcause`, run `python -m app.server`

Any change to a schema must be agreed with the team first — other agents depend on it.
