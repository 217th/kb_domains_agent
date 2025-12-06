from __future__ import annotations

"""
Subagent: Document Processor
- Classifies/fetches content by URL, checks relevance per domain, extracts facts, and saves selected facts.
- Logs hand-offs and key steps; spans instrumented via trace_span.

Public API:
- run_subagent_document_processor(payload): discovery mode (URL→facts) or save mode (selected_fact_ids).

Usage: Requires user_id and raw_text or selected facts. Content tools are real networked; relevance/facts may hit Gemini when RUN_REAL_AI=1. Saves facts via tool_save_fact_to_memory (mock or Firestore when RUN_REAL_MEMORY=1). See docs/subagent_document_processor.json. Emits logs for classification, domain filtering, fact extraction errors, and save batches.
"""

import re
import uuid
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger
from src.utils.telemetry import trace_span
from src.tools.ai_analysis import tool_define_topic_relevance, tool_extract_facts_from_text
from src.tools.content import (
    tool_process_ordinary_page,
    tool_process_pdf_link,
    tool_process_youtube_link,
)
from src.tools.domains import tool_fetch_user_knowledge_domains
from src.tools.memory import tool_save_fact_to_memory
from src.utils.config_loader import load_model_config, load_prompts, load_relevance_threshold

URL_REGEX = re.compile(r"https?://\S+", re.IGNORECASE)
logger = get_logger("subagent_document_processor")


def _first_url(text: str) -> Optional[str]:
    match = URL_REGEX.search(text)
    return match.group(0) if match else None


def _classify_url(url: str) -> str:
    lowered = url.lower()
    if lowered.endswith(".pdf") or "pdf" in lowered:
        return "PDF"
    if "youtube.com/watch" in lowered or "youtu.be/" in lowered:
        return "YOUTUBE"
    return "ORDINARY"


def _fetch_content(url: str, category: str) -> str:
    if category == "PDF":
        response = tool_process_pdf_link({"url": url})
    elif category == "YOUTUBE":
        response = tool_process_youtube_link({"url": url})
    else:
        response = tool_process_ordinary_page({"url": url})
    if response.get("status") != "success":
        return ""
    return response.get("content", "")


def _generate_fact_id(domain_id: str, index: int) -> str:
    return f"{domain_id}_{index}_{uuid.uuid4().hex[:4]}"


@trace_span(span_name="subagent_document_processor_turn", component="subagent_document_processor")
def run_subagent_document_processor(
    payload: Dict[str, Any], session_id: str | None = None, session_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    _ = load_prompts().get("subagent_document_processor")
    _ = load_model_config("subagent_document_processor")
    threshold = load_relevance_threshold("subagent_document_processor")

    if session_state is None:
        raise ValueError("session_state is required (legacy session_manager removed)")
    using_adk_state = True
    state = dict(session_state)
    session_id = session_id or payload.get("session_id")
    original_state = dict(state)
    user_id = state.get("user_id")
    raw_text = payload.get("raw_text")
    selected_fact_ids = payload.get("selected_fact_ids") or []
    facts_payload = payload.get("facts_payload") or []

    if not user_id:
        return _finalize({"reasoning": "Missing user_id.", "status": "error", "error_detail": "user_id_required", "session_id": session_id}, state, original_state, session_id, session_state, using_adk_state)

    # Save mode
    if selected_fact_ids and facts_payload:
        saved = 0
        for fact in facts_payload:
            if fact.get("fact_id") in selected_fact_ids:
                tool_save_fact_to_memory(
                    {
                        "fact_text": fact["content"],
                        "source_url": fact["source_url"],
                        "user_id": user_id,
                        "domain_id": fact["domain_id"],
                    }
                )
                saved += 1
        logger.info(
            "FACT_SAVE_BATCH",
            selected=len(selected_fact_ids),
            attempted=len(facts_payload),
            saved=saved,
            session_id=session_id,
        )
        return _finalize(
            {
                "reasoning": f"Saved {saved} facts.",
                "status": "success",
                "saved_count": saved,
                "session_id": session_id,
            },
            state,
            original_state,
            session_id,
            session_state,
            using_adk_state,
        )

    # Discovery mode
    target_url = state.get("url") or _first_url(raw_text or "")
    if not target_url:
        return _finalize(
            {
                "reasoning": "No URL found in text.",
                "status": "error",
                "error_detail": "url_missing",
                "session_id": session_id,
            },
            state,
            original_state,
            session_id,
            session_state,
            using_adk_state,
        )

    category = _classify_url(target_url)
    state["url_type"] = category
    logger.info("DOC_CLASSIFIED", url=target_url, category=category, session_id=session_id)
    content_text = _fetch_content(target_url, category)
    if not content_text:
        logger.error("CONTENT_FETCH_FAILED", url=target_url, category=category, session_id=session_id)
        state.pop("url", None)
        state.pop("url_type", None)
        return _finalize(
            {
                "reasoning": "Content fetch failed.",
                "status": "error",
                "error_detail": "content_unavailable",
                "session_id": session_id,
            },
            state,
            original_state,
            session_id,
            session_state,
            using_adk_state,
        )

    domains_result = tool_fetch_user_knowledge_domains(
        {"user_id": user_id, "status_filter": "ACTIVE", "view_mode": "DETAILED"}
    )
    if domains_result.get("status") == "empty" or not domains_result.get("data"):
        logger.info("NO_ACTIVE_DOMAINS", user_id=user_id, session_id=session_id)
        state.pop("url", None)
        state.pop("url_type", None)
        return _finalize(
            {"reasoning": "No active domains found.", "status": "no_relevance", "session_id": session_id},
            state,
            original_state,
            session_id,
            session_state,
            using_adk_state,
        )
    logger.info("DOMAINS_RETRIEVED", count=len(domains_result.get("data", [])), user_id=user_id, session_id=session_id)

    candidate_facts: List[Dict[str, Any]] = []
    for domain in domains_result["data"]:
        relevance = tool_define_topic_relevance(
            {
                "content_text": content_text,
                "domain_name": domain["name"],
                "domain_description": domain.get("domain_description", ""),
                "domain_keywords": domain.get("domain_keywords", []),
            }
        )
        if relevance.get("status") != "success" or relevance.get("relevance_score", 0) <= threshold:
            logger.info(
                "DOMAIN_DROPPED",
                domain_id=domain.get("domain_id"),
                domain_name=domain.get("name"),
                score=relevance.get("relevance_score"),
                threshold=threshold,
                session_id=session_id,
            )
            continue

        facts_resp = tool_extract_facts_from_text(
            {
                "content_text": content_text,
                "domain_name": domain["name"],
                "domain_description": domain.get("domain_description", ""),
                "domain_keywords": domain.get("domain_keywords", []),
                "relevance_justification": relevance.get("reasoning", ""),
            }
        )
        if facts_resp.get("status") != "success":
            logger.error(
                "FACT_EXTRACTION_FAILED",
                domain_id=domain.get("domain_id"),
                domain_name=domain.get("name"),
                error_detail=facts_resp.get("error_detail"),
                session_id=session_id,
            )
            continue
        for idx, fact in enumerate(facts_resp.get("facts", [])):
            fact_id = _generate_fact_id(domain["domain_id"], idx)
            candidate_facts.append(
                {
                    "domain_id": domain["domain_id"],
                    "fact_id": fact_id,
                    "content": fact["content"],
                    "source_url": target_url,
                }
            )

    if not candidate_facts:
        logger.info("NO_RELEVANT_FACTS", url=target_url, session_id=session_id)
        state.pop("url", None)
        state.pop("url_type", None)
        return _finalize(
            {"reasoning": "No relevant facts above threshold.", "status": "no_relevance", "session_id": session_id},
            state,
            original_state,
            session_id,
            session_state,
            using_adk_state,
        )

    logger.info("FACTS_EXTRACTED", count=len(candidate_facts), url=target_url, session_id=session_id)
    state.pop("url", None)
    state.pop("url_type", None)
    return _finalize(
        {
        "reasoning": f"Extracted {len(candidate_facts)} candidate facts.",
        "status": "review_required",
        "candidate_facts": candidate_facts,
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
