import os
import uvicorn
from fastmcp import FastMCP
from retail_common.schemas.intake import IntakeOutput
from retail_common.logging_config import get_logger
from app.tools.intake_tools import extract_return_info

logger = get_logger('agent1_intake_server')

mcp = FastMCP('agent1-intake')

@mpp.tool()
def extract_return_info_tool(text: str) -> dict:
    logger.info('Processing return intake for text length=%d', len(text))
    result: IntakeOutput = extract_return_info(text)
    return result.model_dump()


def run_server():
    port = int(os.environ.get('AGENT1_PORT', '8001'))
    host = os.environ.get('AGENT1_HOST', '0.0.0.0')
    logger.info('Starting Agent 1 MCP server on %s:%d', host, port)
    app = mcp.http_app() if hasattr(mcp, 'http_app') else mcp.sse_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    run_server()
