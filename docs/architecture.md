# System Architecture

## Architecture Diagram

```mermaid
graph TD
    UI[Frontend Dashboard<br/>React / Vite / shadcn] -->|HTTP POST /api/v1/returns| A4[Agent 4: Decision & Orch]
    
    A4 -->|MCP Tool: extract_return_info| A1[Agent 1: Intake]
    A4 -->|MCP Tool: analyze_root_cause| A2[Agent 2: Root Cause]
    A4 -->|MCP Tool: retrieve_evidence| A3[Agent 3: Evidence/IR]
    
    A1 -->|FastAPI + spaCy/LLM Fallback| A1_Output[Structured Output + PII Redaction]
    A2 -->|Calibrated LinearSVC| A2_Output[Root Cause Class + Confidence]
    A3 -->|BM25 + TF-IDF + Semantic| A3_Output[Retrieved Evidence + Citations]
    
    A4 -->|Aggregates & LLM Orchestration| Final[Final Recommendation + Escalation Flags]
    
    Final --> UI
    
    subgraph Databases
        Neon[(Neon Postgres Database)]
        VectorDB[(Vector Store)]
    end
    
    A4 --> Neon
    A3 --> VectorDB
```

## Pipeline (reference)
```
Customer return text
        |
        v
[Agent 1: Intake]        --(MCP tool: extract_return_info)-->
        |
        v
[Agent 2: Root Cause]    --(MCP tool: analyze_root_cause)-->
        |
        v
[Agent 3: Evidence/IR]   --(MCP tool: retrieve_evidence)-->
        |
        v
[Agent 4: Decision]      --(MCP tool: generate_final_recommendation)-->
        |
        v
   Frontend dashboard / human reviewer
```
Agents communicate using MCP (Model Context Protocol) over Streamable HTTP.
Agent 4 is both an MCP server (for the frontend) and an MCP client
(it calls Agents 1, 2, and 3 in sequence).
