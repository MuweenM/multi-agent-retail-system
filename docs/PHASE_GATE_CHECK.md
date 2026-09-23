# Phase Gate Check

This is the runbook the team runs together at the end of every phase, before
anyone starts the next one. One person drives (usually Member 4, since they
own Docker Compose and the orchestrator), everyone else is on the call
watching their own lane and ready to fix it live.

A phase is **not done** until its gate check passes clean on a freshly pulled
`dev`. Passing on one person's machine with uncommitted local fixes does not
count.

General rule: merge small PRs into `dev` continuously *during* the phase as
each prompt's own check passes. The gate call is there to verify the
integration of all four lanes together, not to merge four people's work for
the first time live.

---

## 0. Before the call

- [ ] Every lane has merged its Phase N work into `dev` (not sitting on a
      branch).
- [ ] Any shared-file change (schema, taxonomy, analyzer, auth) made during
      this phase was flagged in team chat before its PR, and is reflected in
      `docs/api-contracts.md` if it touched the contract.
- [ ] Each person has run their own lane's "you should see" check from the
      blueprint, locally, and confirms it's green.

## 1. Sync and clean rebuild

```bash
git checkout dev
git pull origin dev
git log --oneline -20        # confirm all 4 lanes' PRs are visible

docker compose down -v       # wipe old containers and volumes
docker compose build --no-cache
```

Wiping volumes and rebuilding without cache catches the "works on my machine
because I have an old container cached" class of false pass.

## 2. Bring the stack up

```bash
docker compose up
```

Watch the logs. Look for:
- All agent containers reach a healthy / listening state
- No crash loops
- No missing-env-var errors (check `.env` has every key from
  `docs/PROJECT_CONTEXT.md`)

## 3. Check each lane in isolation first

Each owner runs their own check in a separate terminal, against the running
containers, not just a local script:

```bash
curl localhost:8001/health
curl localhost:8002/health
curl localhost:8003/health
curl localhost:8004/health

python services/agent1-intake/scripts/call_tool.py   "<sample input>"
python services/agent2-rootcause/scripts/call_tool.py
python services/agent3-retrieval/scripts/call_tool.py
```

If any of these fail, stop here and fix it before testing the chain. A
broken link shows up as a confusing failure downstream otherwise.

## 4. Run the phase's actual gate check

This is the part that changes per phase — pick the block below that matches
where you are. Don't declare the gate passed on vibes; run the command and
read the output.

### Phase 1 gate — "Browser form to decision card, built from three stubs, running in Docker"

```bash
curl -X POST localhost:8004/api/v1/returns \
  -H "Content-Type: application/json" \
  -d '{"text":"phone battery dies fast"}'
```

Confirm:
- [ ] 200, not a timeout or 500
- [ ] Response validates against `DecisionOutput`
- [ ] `agent_trace` shows all 3 agents were actually called (real
      latencies, not zeros from a hardcoded shortcut)

### Phase 2 gate — "Each agent passes its own tests and demos alone"

```bash
pytest services/agent1-intake -q
pytest services/agent2-rootcause -q
pytest services/agent3-retrieval -q
pytest services/agent4-decision -q
```

Each owner also live-demos their agent standalone (client script or its own
UI page against mocks) — this phase does not require the full chain to be
correct yet, only that each piece is independently solid.

- [ ] All four test suites pass on a clean `dev` checkout
- [ ] Each owner's standalone demo runs without errors

### Phase 3 gate — "A 200-row CSV runs end to end and surfaces the planted patterns"

```bash
curl -X POST localhost:8004/api/v1/bulk \
  -F "file=@data/samples/returns_sample.csv" \
  -H "Authorization: Bearer <admin-jwt>"
# poll until status is "done"
curl localhost:8004/api/v1/bulk/<job_id>
```

- [ ] Job completes with `processed` close to 200 (row errors from the 10
      deliberately broken rows are fine, a crash is not)
- [ ] The findings/dashboard surface the planted battery-batch, size-fit and
      courier-spike patterns from `data/PLANTED.md`
- [ ] All four frontend pages (Submit Return, Analytics, Evidence Search,
      the result and bulk-job pages) render against the real API, not just
      mocks

### Phase 4 gate — "Numbers are in docs/evaluation.md, the demo is rehearsed, main is tagged"

```bash
python eval/eval_intake.py
python eval/eval_rootcause.py
python eval/run_eval.py          # retrieval
python eval/eval_e2e.py
```

- [ ] Every table each script produces is actually present in
      `docs/evaluation.md`, not just printed to console
- [ ] `docs/responsible-ai.md`, `docs/commercialization.md`,
      `docs/qa-preparation.md` have no `TODO` markers
- [ ] The team has run the 8-step demo script once, live, start to finish,
      without needing to restart anything

### Phase 5 gate — "With the flag off, behaviour is identical to Phase 4"

```bash
# with ENABLE_SI=false (default) — re-run every Phase 4 check above, unchanged
ENABLE_SI=false docker compose up
pytest -q   # full suite, flag off

# then with the flag on
ENABLE_SI=true docker compose up
python eval/eval_intake.py       # check the +50 Sinhala/Singlish rows
```

- [ ] Every Phase 4 test still passes identically with the flag off
- [ ] With the flag on, the Sinhala/Singlish gold-set numbers are added to
      `docs/evaluation.md`

## 5. If something fails

Common breakages and who owns the fix:

| Symptom | Likely cause | Owner |
|---|---|---|
| Container won't start | Missing/wrong `.env` key, port clash | Whoever's container it is |
| Agent 4 times out calling an agent | Wrong `AGENT{N}_MCP_URL`, not on the same Docker network | Member 4 + that lane |
| Schema validation error | Code doesn't match contract v1.1 exactly | That lane's owner |
| MCP client/server handshake fails | Version mismatch — check `mcp>=1.30,<2` is pinned everywhere | Whoever's on the wrong version |
| Bulk job stalls or crashes | Concurrency bug, or LLM call budget exhausted mid-job | Member 4 |
| A metric looks impossible (e.g. 100% accuracy) | Data leakage, usually resampling done outside the CV fold | That lane's owner |

Fix in place, rebuild just that one container if possible
(`docker compose up --build <service>`), and re-run step 4 without tearing
everything down again.

## 6. Close out the gate

Once the check passes clean:

```bash
git tag phaseN-complete
git push origin phaseN-complete
```

Then update the tracker (see below) with:
- Date and who drove the check
- The actual command output that proved it passed (paste it — this doubles
  as evidence for the report's protocol/evaluation sections)
- Anything fixed live during the call, so it doesn't get re-discovered later

Only after this is logged does anyone start the next phase's prompts.

---

## Shared tracker

Keep a `PROGRESS.md` (or a shared sheet/board) with one row per phase:

| Phase | Gate check run | Result | Date | Driver | Notes |
|---|---|---|---|---|---|
| 1 | curl decision card | ✅ | | | |
| 2 | 4x pytest + demos | | | | |
| 3 | 200-row bulk run | | | | |
| 4 | eval scripts + demo rehearsal | | | | |
| 5 | flag on/off parity | | | | |

This is the single place the whole team looks to answer "are we clear to
start the next phase" — not each person's local checkbox state in the
blueprint artifact, which only they can see.
