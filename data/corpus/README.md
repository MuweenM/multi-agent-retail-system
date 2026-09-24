# Corpus dataset

This corpus is deterministic and seeded for retrieval evaluation. It combines synthetic reviews, supplier quality notes, inventory signals, policy passages, and exported historical returns.

## Source counts

| source_type | count |
| --- | ---: |
| review | 5000 |
| supplier_record | 300 |
| historical_return | 4000 |
| inventory | 200 |
| policy | 15 |

## Planted patterns

- P-014 / S-03 / batch B-2026-07 includes battery swelling defect text.
- P-027 records include the phrase 'runs small' with size-fit labels.
- P-009 review entries include keyword distractor text such as 'great battery life' while remaining neutral.
- Historical returns come from Member 2's `data/returns/returns.csv`, retaining only text fields and excluding customer references.
- Approximately 5% of passages use distractor wording that shares keywords but is semantically different.
- Misspellings are intentionally injected into roughly 8% of review passages.
