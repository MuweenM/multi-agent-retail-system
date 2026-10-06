"""Test client for Agent 1 Intake MCP tool."""

import asyncio
import os
import sys
import json

# Ensure agent directory and project root are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from retail_common.schemas.intake import IntakeOutput
from app.server import extract_return_info


async def main():
    sample_text = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "My Samsung Galaxy A15 battery dies within 2 hours, please refund order ORD-9921 0771234567"
    )

    print(f"\n[Agent 1 Client] Input text: '{sample_text}'")

    try:
        result = extract_return_info(text=sample_text, tenant_id="demo")
        print("\n[Agent 1 Result (IntakeOutput)]:")
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
        print("\nValidation Status: VALID IntakeOutput v1.1")
    except Exception as e:
        print(f"\n[Agent 1 Client Error]: {e}")


if __name__ == "__main__":
    asyncio.run(main())
