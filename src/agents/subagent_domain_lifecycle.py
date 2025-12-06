from __future__ import annotations

"""
Subagent: Domain Lifecycle
- Drafts domain via prettify tool.
- Awaits confirmation; on confirm can persist to Firestore when RUN_REAL_DOMAINS=1, else mock save.

Public API:
- run_subagent_domain_lifecycle(payload): handles CREATE/UPDATE drafts, confirmation flow; returns status/domain_draft/message_to_user.

Usage: Invoked via agent_root or directly. Prettify uses AI (mock or Gemini). Real save requires RUN_REAL_DOMAINS=1 and GCP Firestore setup. See docs/subagent_domain_lifecycle.json for spec. Logs PRETTIFY_FAILED/DOMAIN_WRITE_FAILED on errors.
"""

import os
import random
import string
from typing import Any, Dict, Optional

from google.cloud import firestore

from src.utils.logger import get_logger
from src.utils.telemetry import trace_span
from src.tools.domains import tool_prettify_domain_description
from src.utils.config_loader import ConfigLoader, load_model_config, load_prompts

logger = get_logger("subagent_domain_lifecycle")


def _generate_id(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _persist_domain(doc_id: str, user_id: str, draft: Dict[str, Any]) -> None:
    settings = ConfigLoader.instance().settings
    client = firestore.Client(database=settings.firestore_database or "(default)")
    doc_ref = client.collection("domains").document(doc_id)
    doc_ref.set(
        {
            "user_id": user_id,
            "name": draft["name"],
            "status": "active",
            "domain_description": draft["description"],
            "domain_keywords": draft["keywords"],
        }
    )


@trace_span(span_name="subagent_domain_lifecycle_turn", component="subagent_domain_lifecycle")
def run_subagent_domain_lifecycle(
    payload: Dict[str, Any], session_id: str | None = None, session_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    # Load prompts/model config to keep invocation parameters consistent with the spec.
    _ = load_prompts().get("subagent_domain_lifecycle")
    _ = load_model_config("subagent_domain_lifecycle")

    if session_state is None:
        raise ValueError("session_state is required (legacy session_manager removed)")
    using_adk_state = True
    state = dict(session_state)
    session_id = session_id or payload.get("session_id")
    original_state = dict(state)
    user_id = state.get("user_id")
    domain_id = state.get("domain_id")

    operation_type = payload.get("operation_type")
    user_input = payload.get("user_input", "")
    confirmation_status = bool(payload.get("confirmation_status", False))

    # Validate required fields early; avoid LLM calls when request is malformed.
    if not operation_type or not user_id or not user_input:
        return _finalize(
            {
                "reasoning": "Missing required fields.",
                "status": "READ_ERROR",
                "message_to_user": "operation_type, user_id, and user_input are required.",
                "session_id": session_id,
            },
            state,
            original_state,
            session_id,
            session_state,
            using_adk_state,
        )

    # First phase: ask LLM to prettify the raw intent into a structured draft.
    # This is the draft-generation hop: user text -> LLM prettify -> candidate domain_draft.
    prettified = tool_prettify_domain_description({"raw_input_text": user_input})
    if prettified.get("status") != "SUCCESS":
        logger.error(
            "PRETTIFY_FAILED",
            raw_input=user_input,
            error_details=prettified.get("error_details") or prettified.get("error_detail"),
            session_id=session_id,
        )
        return _finalize(
            {
                "reasoning": "Prettify tool failed.",
                "status": "READ_ERROR",
                "message_to_user": "Could not draft domain. Please retry.",
                "session_id": session_id,
            },
            state,
            original_state,
            session_id,
            session_state,
            using_adk_state,
        )

    # Build draft object; reused across both review and save paths.
    draft = {
        "domain_id": domain_id or _generate_id(),
        "name": prettified["data"]["name"],
        "description": prettified["data"]["description"],
        "keywords": prettified["data"]["keywords"],
    }

    # If user has not confirmed yet, surface the draft for review and stop.
    # Control waits for explicit user confirmation; no persistence occurs in this branch.
    # Confirmation is driven by the caller (agent_root or CLI) setting confirmation_status=True
    # after the user replies with “confirm” (or equivalent) to the presented draft.
    if not confirmation_status:
        state.update({"domain_id": draft["domain_id"], "intent": "DOMAIN_LIFECYCLE"})
        return _finalize(
            {
                "reasoning": "Draft prepared; awaiting user confirmation.",
                "status": "AWAITING_USER_REVIEW",
                "domain_draft": draft,
                "message_to_user": "Review this draft and confirm to save.",
                "session_id": session_id,
            },
            state,
            original_state,
            session_id,
            session_state,
            using_adk_state,
        )

    # Confirmation path: user approved the draft; now decide between real vs. mock save.
    run_real_save = os.getenv("RUN_REAL_DOMAINS") == "1"
    if run_real_save:
        try:
            _persist_domain(draft["domain_id"], user_id, draft)
        except Exception as exc:  # noqa: BLE001
            logger.error("DOMAIN_WRITE_FAILED", error=str(exc), domain_id=draft["domain_id"], session_id=session_id)
            return _finalize(
                {
                    "reasoning": "Failed to persist domain to Firestore.",
                    "status": "WRITE_ERROR",
                    "message_to_user": "Could not save the domain. Please retry later.",
                    "session_id": session_id,
                },
                state,
                original_state,
                session_id,
                session_state,
                using_adk_state,
            )

    # Clear intent after confirmation
    state.pop("intent", None)
    state.pop("domain_id", None)
    return _finalize(
        {
        "reasoning": "User confirmed draft; saved." if run_real_save else "User confirmed draft; mock save performed.",
        "status": "SUCCESS",
        "domain_draft": draft,
        "message_to_user": f"Domain {draft['name']} saved.",
        "session_id": session_id,
        },
        state,
        original_state,
        session_id,
        session_state,
        using_adk_state,
    )


def _finalize(
    resp: Dict[str, Any],
    state: Dict[str, Any],
    original_state: Dict[str, Any],
    session_id: str | None,
    session_state: Optional[Dict[str, Any]],
    using_adk_state: bool,
) -> Dict[str, Any]:
    delta: Dict[str, Any] = {}
    for key in set(original_state.keys()).union(state.keys()):
        if original_state.get(key) != state.get(key):
            delta[key] = state.get(key)

    if delta:
        resp["state_delta"] = delta

    resp.setdefault("session_id", session_id)
    return resp
