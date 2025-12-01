from __future__ import annotations

"""
Subagent: Document Processor
- Classifies/fetches content by URL, checks relevance per domain, extracts facts, and saves selected facts.
- Logs hand-offs and key steps; spans instrumented via trace_span.
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
def run_subagent_document_processor(payload: Dict[str, Any]) -> Dict[str, Any]:
    _ = load_prompts().get("subagent_document_processor")
    _ = load_model_config("subagent_document_processor")
    threshold = load_relevance_threshold("subagent_document_processor")

    user_id = payload.get("user_id")
    raw_text = payload.get("raw_text")
    selected_fact_ids = payload.get("selected_fact_ids") or []
    facts_payload = payload.get("facts_payload") or []

    if not user_id:
        return {"reasoning": "Missing user_id.", "status": "error", "error_detail": "user_id_required"}

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
        )
        return {
            "reasoning": f"Saved {saved} facts.",
            "status": "success",
            "saved_count": saved,
        }

    # Discovery mode
    if not raw_text:
        return {"reasoning": "No raw_text provided for discovery.", "status": "error", "error_detail": "raw_text_missing"}

    target_url = _first_url(raw_text)
    if not target_url:
        return {"reasoning": "No URL found in text.", "status": "error", "error_detail": "url_missing"}

    category = _classify_url(target_url)
    logger.info("DOC_CLASSIFIED", url=target_url, category=category)
    content_text = _fetch_content(target_url, category)
    if not content_text:
        logger.error("CONTENT_FETCH_FAILED", url=target_url, category=category)
        return {"reasoning": "Content fetch failed.", "status": "error", "error_detail": "content_unavailable"}

    domains_result = tool_fetch_user_knowledge_domains(
        {"user_id": user_id, "status_filter": "ACTIVE", "view_mode": "DETAILED"}
    )
    if domains_result.get("status") == "empty" or not domains_result.get("data"):
        logger.info("NO_ACTIVE_DOMAINS", user_id=user_id)
        return {"reasoning": "No active domains found.", "status": "no_relevance"}
    logger.info("DOMAINS_RETRIEVED", count=len(domains_result.get("data", [])), user_id=user_id)

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
        logger.info("NO_RELEVANT_FACTS", url=target_url)
        return {"reasoning": "No relevant facts above threshold.", "status": "no_relevance"}

    logger.info("FACTS_EXTRACTED", count=len(candidate_facts), url=target_url)
    return {
        "reasoning": f"Extracted {len(candidate_facts)} candidate facts.",
        "status": "review_required",
        "candidate_facts": candidate_facts,
    }
