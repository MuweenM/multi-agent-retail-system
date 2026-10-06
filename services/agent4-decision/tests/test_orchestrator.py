import pytest
from unittest.mock import patch, MagicMock
from app.orchestrator import run_orchestrator
from retail_common.schemas import AgentStep

@pytest.mark.asyncio
@patch("app.orchestrator.call_agent")
async def test_agent1_failure_degradation(mock_call_agent):
    mock_call_agent.return_value = (None, AgentStep(agent="agent1-intake", tool="extract", ok=False, latency_ms=100, note="timeout"))
    
    result = await run_orchestrator("bad product", "demo")
    
    assert result.decision == "escalate"
    assert "agent_unavailable:agent1-intake" in result.risk_flags
    assert len(result.agent_trace) == 1
    assert result.agent_trace[0].agent == "agent1-intake"

@pytest.mark.asyncio
@patch("app.orchestrator.call_agent")
async def test_agent2_failure_degradation(mock_call_agent):
    # Agent 1 succeeds, Agent 2 fails
    async def mock_call(url, tool, arguments, agent_name):
        if agent_name == "agent1-intake":
            data = {
                "raw_text": "text", "product": "Valid", "issue": "Broken", "intent": "return", 
                "sentiment": "negative", "confidence": 0.9, "product_match_score": 0.9, 
                "entities": [], "lang": "en", "pii_types_found": [], "flags": []
            }
            return data, AgentStep(agent=agent_name, tool=tool, ok=True, latency_ms=10)
        else:
            return None, AgentStep(agent=agent_name, tool=tool, ok=False, latency_ms=10, note="timeout")
            
    mock_call_agent.side_effect = mock_call
    
    result = await run_orchestrator("broken valid", "demo")
    
    assert result.decision == "escalate"
    assert "agent_unavailable:agent2-rootcause" in result.risk_flags
    assert len(result.agent_trace) == 2
    assert result.agent_trace[1].agent == "agent2-rootcause"

@pytest.mark.asyncio
@patch("app.orchestrator.call_agent")
async def test_agent3_failure_degradation(mock_call_agent):
    # Agent 1, 2 succeed, Agent 3 fails
    async def mock_call(url, tool, arguments, agent_name):
        if agent_name == "agent1-intake":
            data = {
                "raw_text": "text", "product": "Valid", "issue": "Broken", "intent": "return", 
                "sentiment": "negative", "confidence": 0.9, "product_match_score": 0.9, 
                "entities": [], "lang": "en", "pii_types_found": [], "flags": []
            }
            return data, AgentStep(agent=agent_name, tool=tool, ok=True, latency_ms=10)
        elif agent_name == "agent2-rootcause":
            data = {
                "product": "Valid", "issue": "Broken", 
                "candidates": [{"label": "manufacturing_defect", "score": 0.9, "supporting_return_count": 0, "top_terms": []}],
                "top_candidate": "manufacturing_defect", "confidence": 0.9, "model_name": "mock", "model_version": "v1",
                "is_emerging_spike": False, "abuse_risk": 0.1, "notes": []
            }
            return data, AgentStep(agent=agent_name, tool=tool, ok=True, latency_ms=10)
        else:
            return None, AgentStep(agent=agent_name, tool=tool, ok=False, latency_ms=10, note="timeout")
            
    mock_call_agent.side_effect = mock_call
    
    result = await run_orchestrator("broken valid", "demo")
    
    assert result.decision == "escalate"
    assert "agent_unavailable:agent3-retrieval" in result.risk_flags
    assert len(result.agent_trace) == 3
    assert result.agent_trace[2].agent == "agent3-retrieval"
