You are helping me build one agent of a four-agent retail returns system for the course IT 3041 Information Retrieval and Web Analytics. The product is "AI Retail Resolution, Return Root Cause & Intelligence System", built for the Sri Lankan retail market.

Before writing any code, read: README.md, AGENTS.md (or CLAUDE.md / .cursorrules), design.md (frontend work only), docs/api-contracts.md, docs/PROJECT_CONTEXT.md, shared/retail_common/schemas/*.py, shared/retail_common/taxonomy.py, infra/postgres/init.sql, .env.example and data/PLANTED.md.

I do agent 3. I own only services/agent3-retrieval/, the shared files assigned to my lane in the blueprint, and the frontend pages named in my lane. Do not edit anything else. If shared/ or another lane must change, stop and write the change as a short note I can post in team chat.

Facts you must respect:
1. Agents talk MCP over Streamable HTTP. Pin mcp>=1.30,<2 in requirements.txt (mcp 2.x renamed FastMCP to MCPServer and changed the client API). Ports: Agent 1 8001, Agent 2 8002, Agent 3 8003, Agent 4 8004. The browser (port 5173) talks only to Agent 4's REST API.
2. Data contracts are the Pydantic models in shared/retail_common/schemas (contract v1.1). Changes are additive, with defaults. Never rename, retype or remove a field.
3. Root-cause labels, intents, decisions and source types come from shared/retail_common/taxonomy.py. Never invent values.
4. Privacy: raw customer text is seen only by Agent 4 (which stores it encrypted) and by Agent 1 (which redacts it). Everything else, including every LLM call and every log line, sees only `clean_text`.
5. Every MCP tool validates its input, returns a Pydantic model, never raises to the caller (return a structured error instead), logs through get_logger, and accepts tenant_id (default "demo").
6. Course fit: every design choice should map to a lecture topic (tokenization, inverted index, spell correction, TF-IDF and cosine, text classification, evaluation metrics). Name the concept in a short docstring so we can cite it in the report and viva.
7. Frontend: follow AGENTS.md and design.md. shadcn/ui components only, no raw HTML form elements. Build against mock JSON until Agent 4's REST API is ready.

How to work with me: first propose a short plan (files, functions, tests) and wait for my OK. Then implement in small steps with pytest tests. After each step, tell me the exact command to run and the output I should see. Ask at most one question at a time. If a library API is uncertain, check the installed version's documentation instead of guessing.