from mcp.server.mcpserver import MCPServer

from retail_common.schemas.rootcause import RootCauseOutput
from app.tools.rootcause import analyze_root_cause as classify_root_cause


server = MCPServer(name="agent2-rootcause")


@server.tool()
def analyze_root_cause(product: str, issue: str) -> RootCauseOutput:
    return classify_root_cause(product, issue)


if __name__ == "__main__":
    server.run(transport="streamable-http", host="0.0.0.0", port=8002)