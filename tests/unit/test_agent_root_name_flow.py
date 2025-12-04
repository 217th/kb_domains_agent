import sys
from pathlib import Path

import pytest
import os


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))
os.environ["ENABLE_GCP_LOGGING"] = "0"


def test_initial_prompt(monkeypatch):
    from src.agents import agent_root
    res = agent_root.run_agent_root("", session_user_id=None, name_attempts=0)
    assert res["status"] == "AUTH_REQUIRED"
    assert "Hello! Please tell me your name" in res["response_message"]


def test_name_extraction_success(monkeypatch):
    from src.agents import agent_root

    monkeypatch.setattr(
        agent_root,
        "tool_extract_user_name",
        lambda payload: {"status": "success", "name": "Bob", "confidence": "high", "detected": True, "error_detail": None},
    )
    monkeypatch.setattr(
        agent_root,
        "tool_auth_user",
        lambda payload: {"status": "success", "data": {"user_id": "user_bob", "is_new_user": True}},
    )
    monkeypatch.setattr(
        agent_root,
        "tool_fetch_user_knowledge_domains",
        lambda payload: {"status": "success", "data": []},
    )

    res = agent_root.run_agent_root("меня зовут Боб", session_user_id=None, name_attempts=0)
    assert res["status"] == "SUCCESS"
    assert res.get("authenticated_user_id") == "user_bob"
    assert res.get("name_attempts") == 1


def test_name_extraction_max_attempts(monkeypatch):
    from src.agents import agent_root

    monkeypatch.setattr(
        agent_root,
        "tool_extract_user_name",
        lambda payload: {"status": "error", "name": None, "confidence": None, "detected": False, "error_detail": "NAME_NOT_DETECTED"},
    )

    res1 = agent_root.run_agent_root("hi", session_user_id=None, name_attempts=0)
    assert res1["status"] == "AUTH_REQUIRED"
    assert res1["name_attempts"] == 1

    res2 = agent_root.run_agent_root("hello", session_user_id=None, name_attempts=1)
    assert res2["status"] == "AUTH_REQUIRED"
    assert res2["name_attempts"] == 2

    res3 = agent_root.run_agent_root("again", session_user_id=None, name_attempts=2)
    assert res3["status"] == "AUTH_REQUIRED"
    assert "Access denied" in res3["response_message"]
    assert res3["name_attempts"] == 3
