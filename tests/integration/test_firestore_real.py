import os
import sys
import uuid
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))


def _firestore_client():
    from google.cloud import firestore
    db = os.getenv("FIRESTORE_DATABASE") or "(default)"
    return firestore.Client(database=db)


def test_auth_user_creates_and_reuses():
    from src.tools.auth import tool_auth_user

    username = f"integration_user_{uuid.uuid4().hex[:6]}"
    first = tool_auth_user({"username": username})
    assert first["status"] == "success"
    assert first["data"]["is_new_user"] is True
    user_id = first["data"]["user_id"]

    second = tool_auth_user({"username": username})
    assert second["status"] == "success"
    assert second["data"]["is_new_user"] is False
    assert second["data"]["user_id"] == user_id


def test_domain_fetch_and_toggle_roundtrip():
    from src.tools.domains import tool_fetch_user_knowledge_domains, tool_toggle_domain_status

    client = _firestore_client()
    user_id = f"u_{uuid.uuid4().hex[:6]}"
    domain_doc = client.collection("domains").document()
    domain_doc.set(
        {
            "user_id": user_id,
            "name": "Integration Domain",
            "status": "active",
            "domain_description": "Desc",
            "domain_keywords": ["k1", "k2"],
        }
    )

    fetched = tool_fetch_user_knowledge_domains({"user_id": user_id, "status_filter": "ACTIVE", "view_mode": "DETAILED"})
    assert fetched["status"] == "success"
    assert fetched["data"][0]["domain_id"] == domain_doc.id

    toggle = tool_toggle_domain_status({"user_id": user_id, "domain_id": domain_doc.id})
    assert toggle["status"] == "success"
    assert toggle["data"]["previous_status"] != toggle["data"]["new_status"]
