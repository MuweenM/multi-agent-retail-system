import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from mcp.server.fastmcp import FastMCP
from shared.retail_common.schemas.evidence import EvidenceOutput, EvidenceItem

server = FastMCP(
    name="agent3-retrieval",
    host="0.0.0.0",
    port=8003,
    streamable_http_path="/mcp",
)

@server.tool()
def retrieve_evidence(
    query: str,
    top_k: int = 3,
    method: str = "hybrid"
) -> EvidenceOutput:
    """Retrieve evidence from the knowledge base."""
    # Stub implementation for Phase 1
    return EvidenceOutput(
        query=query,
        evidence=[
            EvidenceItem(
                source_type="doc",
                source_id="doc-123",
                snippet="battery drain issue reported for this product.",
                relevance_score=0.95
            )
        ],
        total_results=1,
        method=method
    )

if __name__ == "__main__":
    server.run(transport="streamable-http")
