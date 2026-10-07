import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT3_DIR = ROOT / "services" / "agent3-retrieval"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(AGENT3_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT3_DIR))

from app.ir.tolerant import process_query
from app.ir.hybrid import HybridRanker

rows = [json.loads(line) for line in Path('data/corpus/corpus.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
print(process_query('battrry swlling on powerbank'))
ranker = HybridRanker(rows)
for h in ranker.rank('battrry swlling on powerbank', top_k=5):
    print(h.doc_id, h.source_type, h.score, h.title)
