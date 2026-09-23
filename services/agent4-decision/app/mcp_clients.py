import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import time
import json
import asyncio
from typing import Any
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from shared.retail_common.schemas import AgentStep
from shared.retail_common.logging_config import get_logger

logger = get_logger("mcp_clients")

async def call_agent(url: str, tool: str, arguments: dict[str, Any], agent_name: str, timeout: int = 20, retries: int = 1) -> tuple[dict[str, Any] | None, AgentStep]:
    """
    Calls an MCP agent over streamable HTTP, returning the parsed JSON result and an AgentStep.
    """
    start_time = time.time()
    ok = False
    note = ""
    result_data = None
    
    for attempt in range(retries + 1):
        try:
            async with streamable_http_client(url) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    
                    result = await asyncio.wait_for(
                        session.call_tool(tool, arguments),
                        timeout=timeout
                    )
                    
                    if not result.isError and result.content:
                        text_content = next((c.text for c in result.content if c.type == "text"), None)
                        if text_content:
                            result_data = json.loads(text_content)
                            ok = True
                            note = "success"
                        else:
                            note = "no text content"
                    else:
                        note = "tool returned error"
                        logger.error(f"{agent_name} {tool} returned error: {result}")
                    break
        except Exception as e:
            logger.error(f"Error calling {agent_name} at {url} (attempt {attempt + 1}): {e}")
            note = str(e)
            if attempt == retries:
                break
            await asyncio.sleep(1)
            
    latency_ms = int((time.time() - start_time) * 1000)
    step = AgentStep(
        agent=agent_name,
        tool=tool,
        ok=ok,
        latency_ms=latency_ms,
        note=note[:100]
    )
    
    return result_data, step
