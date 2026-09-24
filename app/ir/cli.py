from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.ir.inverted_index import InvertedIndex


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Boolean and positional retrieval over the seeded corpus.")
    parser.add_argument("query", help="Boolean query such as 'battery AND swelling' or quoted phrase query.")
    parser.add_argument("--corpus", default=str(Path(__file__).resolve().parents[2] / "data" / "corpus" / "corpus.jsonl"))
    parser.add_argument("--product", dest="product_id")
    parser.add_argument("--supplier")
    parser.add_argument("--source-type")
    parser.add_argument("--from-date")
    parser.add_argument("--to-date")
    parser.add_argument("--zone", choices=["title", "body", "supplier_notes", "all"], default="all")
    parser.add_argument("--limit", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    index = InvertedIndex.from_jsonl(Path(args.corpus))
    result = index.search(
        args.query,
        product_id=args.product_id,
        supplier_id=args.supplier,
        source_type=args.source_type,
        start_date=args.from_date,
        end_date=args.to_date,
        zone=args.zone,
        limit=args.limit,
    )
    payload = {
        "query": args.query,
        "count": len(result["docs"]),
        "docs": result["docs"],
        "comparisons_saved": result.get("comparisons_saved", 0),
        "build_time": result.get("build_time"),
        "index_size_bytes": result.get("index_size_bytes"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
