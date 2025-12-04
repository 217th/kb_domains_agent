import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))


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

    result = run_agent_root("Alice", name_attempts=1)
    assert result["status"] == "SUCCESS"
    assert "domains" in result["response_message"]
    assert result.get("authenticated_user_id") == "user_mock"


def test_agent_root_url_delegation():
    from src.agents.agent_root import run_agent_root

    result = run_agent_root("Check this http://example.com", session_user_id="user_123")
    assert result["status"] == "DELEGATE"
    assert result["delegation_target"] == "subagent_document_processor"
    payload = result["delegation_payload"]
    assert payload["target_url"].startswith("http://example.com")
    assert payload["user_id"] == "user_123"
