import sys
from pathlib import Path
import os

import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))
os.environ["ENABLE_GCP_LOGGING"] = "0"
os.environ.setdefault("RUN_REAL_AI", "0")


def test_document_processor_discovery_flow(monkeypatch):
    from src.agents import subagent_document_processor

    def fake_fetch_domains(payload):
        return {
            "status": "success",
            "data": [
                {
                    "domain_id": "dom_ai",
                    "name": "AI Research",
                    "domain_description": "AI desc",
                    "domain_keywords": ["AI"],
                }
            ],
        }

    def fake_relevance(payload):
        return {"status": "success", "relevance_score": 0.9, "reasoning": "relevant", "error_detail": None}

    def fake_extract(payload):
        return {
            "status": "success",
            "facts": [
                {"fact_id": "f1", "content": "c1", "justification": "j1"},
                {"fact_id": "f2", "content": "c2", "justification": "j2"},
            ],
            "extracted_count": 2,
            "error_detail": None,
        }

    def fake_process_page(payload):
        return {"status": "success", "content": "AI content", "page_title": "t"}

    monkeypatch.setattr(subagent_document_processor, "tool_fetch_user_knowledge_domains", fake_fetch_domains)
    monkeypatch.setattr(subagent_document_processor, "tool_define_topic_relevance", fake_relevance)
    monkeypatch.setattr(subagent_document_processor, "tool_extract_facts_from_text", fake_extract)
    monkeypatch.setattr(subagent_document_processor, "tool_process_pdf_link", fake_process_page)
    monkeypatch.setattr(subagent_document_processor, "tool_process_youtube_link", fake_process_page)
    monkeypatch.setattr(subagent_document_processor, "tool_process_ordinary_page", fake_process_page)

    session_id = "sess_e2e_doc_discovery"
    state = {"user_id": "user_1", "url": "http://example.com/article"}
    result = subagent_document_processor.run_subagent_document_processor(
        {"session_id": session_id, "raw_text": "Here is a link http://example.com/article"},
        session_id=session_id,
        session_state=state,
    )
    assert result["status"] == "review_required"
    facts = result["candidate_facts"]
    assert len(facts) >= 2
    assert all(f["source_url"].startswith("http") for f in facts)


def test_document_processor_save_flow(monkeypatch):
    from src.agents import subagent_document_processor

    saved_calls = []

    def fake_save(payload):
        saved_calls.append(payload)
        return {"status": "success", "data": {"memory_id": "mem_123"}}

    monkeypatch.setattr(subagent_document_processor, "tool_save_fact_to_memory", fake_save)

    facts_payload = [
        {"domain_id": "dom_ai", "fact_id": "f1", "content": "c1", "source_url": "http://x"},
        {"domain_id": "dom_ai", "fact_id": "f2", "content": "c2", "source_url": "http://x"},
    ]
    session_id = "sess_e2e_doc_save"
    state = {"user_id": "user_1"}
    result = subagent_document_processor.run_subagent_document_processor(
        {"session_id": session_id, "selected_fact_ids": ["f1", "f2"], "facts_payload": facts_payload},
        session_id=session_id,
        session_state=state,
    )
    assert result["status"] == "success"
    assert result["saved_count"] == 2
    assert len(saved_calls) == 2
