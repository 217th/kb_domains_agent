import sys
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))
os.environ["ENABLE_GCP_LOGGING"] = "0"


def test_agent_root_auth_flow(monkeypatch):
    from src import agents
    from src.agents.agent_root import run_agent_root

    def fake_auth(payload):
        return {"status": "success", "data": {"user_id": "user_mock", "is_new_user": True}, "error": None}

    def fake_fetch(payload):
        return {
            "status": "success",
            "data": [
                {"domain_id": "dom1", "name": "AI", "status": "active"},
                {"domain_id": "dom2", "name": "Energy", "status": "inactive"},
            ],
        }

    def fake_name(payload):
        return {"status": "success", "name": "Alice", "confidence": "high", "detected": True, "error_detail": None}

    monkeypatch.setattr(agents.agent_root, "tool_auth_user", fake_auth)
    monkeypatch.setattr(agents.agent_root, "tool_fetch_user_knowledge_domains", fake_fetch)
    monkeypatch.setattr(agents.agent_root, "tool_extract_user_name", fake_name)

    session_id = "sess_e2e_root"
    state = {}
    result = run_agent_root("Alice", session_state=state, session_id=session_id)
    assert result["status"] == "SUCCESS"
    assert "domains" in result["response_message"]
    assert result.get("authenticated_user_id") == "user_mock"
    assert result.get("session_id") == session_id


def test_agent_root_url_delegation():
    from src.agents.agent_root import run_agent_root
    session_id = "sess_e2e_url"
    state = {"user_id": "user_123"}
    result = run_agent_root("Check this http://example.com", session_state=state, session_id=session_id)
    assert result["status"] == "DELEGATE"
    assert result["delegation_target"] == "subagent_document_processor"
    payload = result["delegation_payload"]
    assert payload["session_id"] == session_id
