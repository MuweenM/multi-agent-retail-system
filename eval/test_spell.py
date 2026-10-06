import asyncio
from ir_system.ir.tolerant import TolerantQueryProcessor
proc = TolerantQueryProcessor()
res = proc.process('batt* swelin')
print("batt* swelin ->", res["corrected_query"])
res = proc.process('battrry defct')
print("battrry defct ->", res["corrected_query"])
