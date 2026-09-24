"""Call the retrieval MCP tool directly for local smoke tests."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.agent3_retrieval.app.server import retrieve_evidence


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "battery drains quickly and overheats"
    result = retrieve_evidence(query=query, top_k=5, method="hybrid", tenant_id="demo")
    print(result.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
