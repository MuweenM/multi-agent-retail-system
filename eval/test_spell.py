import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT3_DIR = ROOT / "services" / "agent3-retrieval"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "shared") not in sys.path:
    sys.path.insert(0, str(ROOT / "shared"))
if str(AGENT3_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT3_DIR))

from app.ir.tolerant import TolerantQueryProcessor
proc = TolerantQueryProcessor()
res = proc.process('batt* swelin')
print("batt* swelin ->", res["corrected_query"])
res = proc.process('battrry defct')
print("battrry defct ->", res["corrected_query"])
