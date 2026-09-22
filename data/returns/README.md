# Labelled Returns Dataset

`returns.csv` is a deterministic, seeded synthetic dataset for Agent 2 Phase 2.
It contains 4,000 English-only return records with slot-filled templates, realistic
typos, uppercase examples, limited Latin-script Singlish, approximately 5% label
noise, and a 30% optional LLM-text path using the shared `call_llm` mechanism in
batches of 20. If credentials or the provider are unavailable, the generator keeps
the deterministic template text so local evaluation remains reproducible.

The generator reads `DATASET_TODAY` and plants the five stories in `data/PLANTED.md`:
P-014 battery swelling, P-027 fit problems, the C-2 electronics damage spike, twelve
repeat-return customer references, and the P-009 noise-cancelling listing distractor.
Only values from `shared/retail_common/taxonomy.py` are used as gold labels.

`district` is included as descriptive metadata only and must never be used as a model
feature. Customer references are synthetic. The loader hashes them before database
storage and writes the gold label to `root_cause_gold`; it is safe to rerun through
an upsert on `return_id`.

The current v1.1 database migration does not include CSV-only `order_id` or `channel`
columns and does not permit plaintext customer references. Those fields remain in the
CSV for evaluation and are not silently added to shared schema files by this lane.

Generate locally with:

```powershell
.\.venv\Scripts\python.exe data/returns/generate_returns.py
```

Load into PostgreSQL with:

```powershell
.\.venv\Scripts\python.exe data/returns/load_returns.py
```
