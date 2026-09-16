# AI Retail Resolution, Return Root Cause & Intelligence System

IT 3041 — Information Retrieval and Web Analytics | Sector: Retail Technology

Skeleton repo for a 4-agent system communicating over **MCP (Model
Context Protocol)**. This repo contains only the folder structure and
common configuration everyone shares — **no agent logic is pre-built**.
Each of the 4 team members implements one agent from scratch, guided by
that agent's own `README.md`.

## Team assignment

| Agent | Folder | Role |
|---|---|---|
| 1 | `services/agent1-intake/` | NLP extraction (product, issue, intent, sentiment) |
| 2 | `services/agent2-rootcause/` | Root-cause pattern analysis |
| 3 | `services/agent3-retrieval/` | Evidence retrieval (Information Retrieval core) |
| 4 | `services/agent4-decision/` | MCP client/orchestrator + final recommendation |

Frontend (`frontend/`) can be split across the team or owned by whoever
has bandwidth — it depends on Agent 4 being ready.

**Read your own agent's `README.md` first** — it's a full spec of what
to build, the exact input/output contract, and a checklist.

## First-time setup (everyone does this once)

1. Clone the repo:
   ```bash
   git clone <repo-url>
   cd retail-return-intelligence
   ```
2. Copy the environment template and fill in the values **as a team**
   (agree on DB credentials, LLM provider, etc. together — don't pick
   your own, since everyone's `.env` needs to work together):
   ```bash
   cp .env.example .env
   ```
3. Install the shared package (every agent depends on this):
   ```bash
   pip install -e shared
   ```
4. Create your own branch for your agent:
   ```bash
   git checkout -b <your-name>/<agent-name>
   ```

## Repo structure

```
retail-return-intelligence/
├── shared/               # COMMON — schemas, config, LLM client, DB session (ready to use)
├── services/
│   ├── agent1-intake/    # Member 1 builds this — see its README.md
│   ├── agent2-rootcause/ # Member 2 builds this — see its README.md
│   ├── agent3-retrieval/ # Member 3 builds this — see its README.md
│   └── agent4-decision/  # Member 4 builds this — see its README.md
├── frontend/             # Team builds this together — see its README.md
├── infra/                # docker-compose, Postgres init.sql (common config)
├── data/                 # synthetic data generation (coordinate as a team)
├── docs/                 # architecture, contracts, Responsible AI, evaluation
└── .github/workflows/    # CI — runs automatically on PRs
```

## What's common (already working, don't rebuild)
- `shared/retail_common/config.py` — reads your `.env`, exposes `settings`
- `shared/retail_common/logging_config.py` — `get_logger(name)`
- `shared/retail_common/db.py` — Postgres session (`SessionLocal`, `get_db()`)
- `shared/retail_common/llm_client.py` — `call_llm(prompt, system, max_tokens)`
- `shared/retail_common/schemas/` — the 4 data contracts every agent must satisfy
- `docker-compose.yml` — brings up Postgres + all 4 agents + frontend together
- `infra/postgres/init.sql` — creates the database tables

## The contract — read this before writing any code
Every agent's input/output MUST match the Pydantic models in
`shared/retail_common/schemas/`. Open these as a team FIRST and agree
on the fields before anyone starts coding — changing them later means
every agent downstream breaks.

| Agent | MCP tool name | Input | Output schema |
|---|---|---|---|
| 1 | `extract_return_info` | `text: str` | `IntakeOutput` |
| 2 | `analyze_root_cause` | `product: str, issue: str` | `RootCauseOutput` |
| 3 | `retrieve_evidence` | `query: str, top_k: int, method: str` | `EvidenceOutput` |
| 4 | `generate_final_recommendation` | `return_text: str` | `DecisionOutput` |

## Running things once your agent is built
```bash
python app/server.py     # run just your agent locally
make up                    # docker-compose up --build (once everyone's agent has code)
make test-all               # run all agents' tests
```

## Team workflow
- `main` = stable/demo-ready only. `dev` = integration branch.
- One branch per person: `git checkout -b agent1/nlp-extraction`
- Open a PR into `dev`, get one teammate's review, then merge.
- If you need to change a shared schema, message the team first —
  everyone else's agent depends on those exact field names.
