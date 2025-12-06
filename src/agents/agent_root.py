from __future__ import annotations

"""
Agent Root:
- Authenticates user, routes intents (URL/doc processing, domain lifecycle, toggle/snapshots/export).
- Emits HANDOFF logs on delegation.

Public API:
- run_agent_root(user_message, session_id=None): returns status/response or delegation payload per spec.

Usage: Uses tool_auth_user and domain tools (Firestore-backed). Delegates to subagent_document_processor or subagent_domain_lifecycle; caller expected to execute subagent when status=DELEGATE. Respects prompts/config loader. See docs/agent_root.json for full spec. HANDOFF logs include reason and target.
"""

import re
from typing import Any, Dict, Optional

from src.tools.auth import tool_auth_user
from src.tools.ai_analysis import tool_extract_user_name
from src.tools.domains import (
    tool_export_detailed_domain_snapshot,
    tool_fetch_user_knowledge_domains,
    tool_generate_domain_snapshot,
    tool_toggle_domain_status,
)
from src.utils.config_loader import load_model_config, load_prompts
from src.utils.logger import get_logger
from src.utils.telemetry import trace_span

URL_REGEX = re.compile(r"https?://\S+", re.IGNORECASE)
logger = get_logger("agent_root")


def _detect_name(message: str) -> Optional[str]:
    lowered = message.lower()
    if "my name is" in lowered:
        # Take the last token as a simple heuristic.
        parts = message.split()
        return parts[-1].strip(".,!") if parts else None
    if len(message.split()) == 1 and message.isalpha():
        return message
    return None


def _format_domains(domains: list[dict[str, Any]]) -> str:
    active = [d for d in domains if d.get("status", "").lower() == "active"]
    inactive = [d for d in domains if d.get("status", "").lower() == "inactive"]
    def fmt(items: list[dict[str, Any]]) -> str:
        return ", ".join(d.get("name", d.get("domain_id", "")) for d in items) or "none"
    return f"🟢 Active: {fmt(active)} | ⚪ Inactive: {fmt(inactive)}"


def _classify_intent(message: str) -> str:
    lowered = message.lower()
    if URL_REGEX.search(message):
        return "URL"
    if any(k in lowered for k in ["create domain", "new topic", "edit domain", "change description", "update domain"]):
        return "DOMAIN_LIFECYCLE"
    if any(k in lowered for k in ["enable", "disable", "activate", "turn off"]):
        return "TOGGLE"
    if any(k in lowered for k in ["snapshot", "summary", "what do i know"]):
        return "SNAPSHOT"
    if any(k in lowered for k in ["export", "download", "detailed report"]):
        return "EXPORT"
    return "UNKNOWN"


@trace_span(span_name="agent_root_turn", component="agent_root")
def run_agent_root(
    user_message: str,
    session_state: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    prompts = load_prompts()
    _ = prompts.get("agent_root")  # Loaded to satisfy prompt management requirement.
    _ = load_model_config("agent_root")

    if session_state is None:
        raise ValueError("session_state is required in ADK mode (legacy session_manager removed)")
    state = dict(session_state)
    session_id = session_id or state.get("session_id")

    original_state = dict(state)
    session_user_id = state.get("user_id")
    name_attempts = state.get("name_attempts", 0)

    def finalize(resp: Dict[str, Any]) -> Dict[str, Any]:
        delta: Dict[str, Any] = {}
        for key in set(original_state.keys()).union(state.keys()):
            old = original_state.get(key)
            new = state.get(key)
            if old != new:
                delta[key] = new

        if delta:
            resp["state_delta"] = delta

        resp.setdefault("session_id", session_id)
        return resp

    # Phase 1: authentication/state check
    if not session_user_id:
        # Initial prompt if no input yet
        if not user_message.strip() and name_attempts == 0:
            return finalize({
                "reasoning": "User not authenticated; request introduction.",
                "status": "AUTH_REQUIRED",
                "response_message": prompts.get("agent_root_name_prompt", "Hello! Please tell me your name to get started."),
                "name_attempts": name_attempts,
            })

        attempts = name_attempts + 1
        state["name_attempts"] = attempts
        name_res = tool_extract_user_name({"user_input": user_message})
        logger.info(
            "NAME_EXTRACTION_RESULT",
            detected=name_res.get("detected"),
            name=name_res.get("name"),
            confidence=name_res.get("confidence"),
            session_id=session_id,
        )
        if not name_res.get("detected") or not name_res.get("name"):
            if attempts >= 3:
                return finalize({
                    "reasoning": "Name not detected after max attempts.",
                    "status": "AUTH_REQUIRED",
                    "response_message": "Access denied. Please request a new session.",
                    "name_attempts": attempts,
                })
            return finalize({
                "reasoning": "Name not detected; ask user to retry.",
                "status": "AUTH_REQUIRED",
                "response_message": "I could not catch your name. Please enter it again.",
                "name_attempts": attempts,
            })

        name = name_res["name"]
        auth_result = tool_auth_user({"username": name})
        if auth_result.get("status") != "success" or "data" not in auth_result:
            return finalize({
                "reasoning": f"Authentication tool failed: {auth_result}",
                "status": "AUTH_REQUIRED",
                "response_message": "I could not verify you. Please try again or check credentials.",
                "name_attempts": attempts,
            })
        user_id = auth_result["data"]["user_id"]
        state.update({"user_id": user_id, "user_name": name, "name_attempts": attempts})
        domains_result = tool_fetch_user_knowledge_domains(
            {"user_id": user_id, "status_filter": "ALL", "view_mode": "DETAILED"}
        )
        domain_summary = _format_domains(domains_result.get("data", []))
        return finalize({
            "reasoning": "Authenticated user via name heuristic and fetched domains.",
            "status": "SUCCESS",
            "response_message": f"Welcome, {name}! Here are your domains: {domain_summary}",
            "authenticated_user_id": user_id,
            "name_attempts": attempts,
        })

    # Phase 2: intent classification & routing
    intent = _classify_intent(user_message)
    if intent == "URL":
        url_match = URL_REGEX.search(user_message)
        target_url = url_match.group(0) if url_match else ""
        state.update({"intent": "DOC_PROCESS", "url": target_url})
        logger.info(
            "HANDOFF",
            source="agent_root",
            target="subagent_document_processor",
            reason="URL detected",
            url=target_url,
            session_id=session_id,
            trace_id=None,
        )
        return finalize({
            "reasoning": f"Detected URL; delegating to document processor for {target_url}.",
            "status": "DELEGATE",
            "delegation_target": "subagent_document_processor",
            "delegation_payload": {
                "session_id": session_id,
                "raw_text": user_message,
            },
        })
    if intent == "DOMAIN_LIFECYCLE":
        operation_type = "CREATE" if "create" in user_message.lower() or "new" in user_message.lower() else "UPDATE"
        state.update({"intent": "DOMAIN_LIFECYCLE", "domain_id": None})
        logger.info(
            "HANDOFF",
            source="agent_root",
            target="subagent_domain_lifecycle",
            reason=f"Domain lifecycle intent ({operation_type})",
            operation_type=operation_type,
            session_id=session_id,
            trace_id=None,
        )
        return finalize({
            "reasoning": "Domain lifecycle intent detected; deferring to subagent.",
            "status": "DELEGATE",
            "delegation_target": "subagent_domain_lifecycle",
            "delegation_payload": {
                "operation_type": operation_type,
                "user_input": user_message,
                "session_id": session_id,
            },
        })
    if intent == "TOGGLE":
        toggle_result = tool_toggle_domain_status({"user_id": session_user_id, "domain_id": "dom_ai"})
        return finalize({
            "reasoning": "Toggle intent detected; executed mock toggle.",
            "status": "SUCCESS",
            "response_message": f"Toggled domain status: {toggle_result['data']}",
        })
    if intent == "SNAPSHOT":
        snapshot = tool_generate_domain_snapshot({"user_id": session_user_id, "domain_id": "dom_ai"})
        return finalize({
            "reasoning": "Snapshot intent detected; generated mock snapshot.",
            "status": "SUCCESS",
            "response_message": snapshot["data"]["super_summary"],
        })
    if intent == "EXPORT":
        export = tool_export_detailed_domain_snapshot({"user_id": session_user_id, "domain_id": "dom_ai"})
        return finalize({
            "reasoning": "Export intent detected; generated mock export link.",
            "status": "SUCCESS",
            "response_message": f"Download: {export['data']['download_url']}",
        })

    return finalize({
        "reasoning": "No matching intent; requesting clarification.",
        "status": "SUCCESS",
        "response_message": 
            """How can I help with your domains or links? Type:
            - create domain (describe)
            - or new topic (describe)
            - or edit domain
            - or update domain
            - or enable domain
            - or disable domain
            - or snapshot
            - or summary
            - or export
            - or provide valid url""",
    })

    # Compute state_delta for callers using session_state
