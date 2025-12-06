"""
Session management helpers built on ADK InMemorySessionService.

Main helpers:
- ensure_session(session_id=None): returns (session_id, session), creating one when missing.
- get_state(session_id): returns current session.state dict.
- update_state(session_id, updates=None, clear_keys=None): merges/removes keys in session.state.

Notes:
- Uses a single app_name and a fixed service-level user bucket ("anonymous") since user_id
  is tracked inside session.state per business requirements. Session IDs are server-generated.
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Iterable, Optional

from google.adk.sessions.in_memory_session_service import InMemorySessionService

APP_NAME = os.getenv("ADK_APP_NAME", "kb_domains_agent")
_SERVICE_USER_ID = "anonymous"
_session_service: Optional[InMemorySessionService] = None


def get_session_service() -> InMemorySessionService:
    global _session_service
    if _session_service is None:
        _session_service = InMemorySessionService()
    return _session_service


def ensure_session(session_id: Optional[str] = None) -> tuple[str, Any]:
    """
    Ensure a session exists; returns (session_id, Session).
    When session_id is missing or not found, a new session is created.
    """
    service = get_session_service()
    target_session_id = session_id or str(uuid.uuid4())
    session = service.get_session_sync(app_name=APP_NAME, user_id=_SERVICE_USER_ID, session_id=target_session_id)
    if session is None:
        session = service.create_session_sync(
            app_name=APP_NAME,
            user_id=_SERVICE_USER_ID,
            session_id=target_session_id,
            state={},
        )
    return session.id, session


def _get_storage_state(session_id: str) -> Dict[str, Any]:
    service = get_session_service()
    ensure_session(session_id)
    storage = service.sessions.setdefault(APP_NAME, {}).setdefault(_SERVICE_USER_ID, {})
    if session_id not in storage:
        storage[session_id] = service.create_session_sync(
            app_name=APP_NAME, user_id=_SERVICE_USER_ID, session_id=session_id, state={}
        )
    return storage[session_id].state


def get_state(session_id: str) -> Dict[str, Any]:
    """
    Returns a shallow copy of session.state; always non-None.
    """
    service = get_session_service()
    session = service.get_session_sync(app_name=APP_NAME, user_id=_SERVICE_USER_ID, session_id=session_id)
    if session is None:
        return {}
    return dict(session.state or {})


def update_state(session_id: str, updates: Optional[Dict[str, Any]] = None, clear_keys: Optional[Iterable[str]] = None) -> None:
    """
    Merge updates into session.state and/or remove listed keys.
    """
    state = _get_storage_state(session_id)
    if updates:
        state.update({k: v for k, v in updates.items() if v is not None})
    if clear_keys:
        for key in clear_keys:
            state.pop(key, None)
