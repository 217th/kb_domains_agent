from __future__ import annotations

"""
Auth tool (Firestore-backed): looks up user by username, creates if missing.

Public API:
- tool_auth_user(payload): validates username, queries Firestore `users`, creates if absent; returns status/data/error per spec.

Usage: requires GOOGLE_APPLICATION_CREDENTIALS/GOOGLE_CLOUD_PROJECT and FIRESTORE_DATABASE. Obeys RUN_REAL modes implicitly (always real Firestore). Errors are returned in response; caller should handle AUTH failures gracefully. See docs/tool_auth_user.json for detailed schema.
"""

from typing import Any, Dict

from google.cloud import firestore
from google.cloud.firestore import Client
from pydantic import BaseModel, Field

from src.utils.config_loader import ConfigLoader


class AuthUserRequest(BaseModel):
    username: str


class AuthUserData(BaseModel):
    user_id: str
    is_new_user: bool


class AuthUserResponse(BaseModel):
    status: str = Field(default="success")
    data: AuthUserData
    error: str | None = None


def _ensure_request(payload: AuthUserRequest | Dict[str, Any]) -> AuthUserRequest:
    return payload if isinstance(payload, AuthUserRequest) else AuthUserRequest(**payload)


def _get_client() -> Client:
    settings = ConfigLoader.instance().settings
    return firestore.Client(database=settings.firestore_database or "(default)")


def tool_auth_user(payload: AuthUserRequest | Dict[str, Any]) -> Dict[str, Any]:
    """
    Real Firestore-backed auth: lookup by username, create if missing.
    """
    req = _ensure_request(payload)
    client = _get_client()
    try:
        query = (
            client.collection("users")
            .where("username", "==", req.username)
            .limit(1)
            .stream()
        )
        existing = next(query, None)
        if existing:
            return AuthUserResponse(
                status="success",
                data=AuthUserData(user_id=existing.id, is_new_user=False),
                error=None,
            ).model_dump()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"QUERY_FAILED: {exc}"}

    try:
        doc_ref = client.collection("users").document()
        doc_ref.set({"username": req.username})
        return AuthUserResponse(
            status="success",
            data=AuthUserData(user_id=doc_ref.id, is_new_user=True),
            error=None,
        ).model_dump()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"USER_CREATION_FAILED: {exc}"}
