from __future__ import annotations

"""
AI analysis tools:
- Relevance scoring, fact extraction, and domain prettify.
- Mock by default; real Gemini calls when RUN_REAL_AI=1 using google-generativeai.
"""

import json
import os
from typing import Any, Dict, List

import google.generativeai as genai
from pydantic import BaseModel, Field

from src.utils.config_loader import ConfigLoader, load_model_config, load_relevance_threshold


class RelevanceRequest(BaseModel):
    content_text: str
    domain_name: str
    domain_description: str
    domain_keywords: List[str]


class RelevanceResponse(BaseModel):
    status: str
    relevance_score: float
    reasoning: str
    error_detail: str | None = None


class ExtractFactsRequest(BaseModel):
    content_text: str
    domain_name: str
    domain_description: str
    domain_keywords: List[str]
    relevance_justification: str


class Fact(BaseModel):
    fact_id: str
    content: str
    justification: str


class ExtractFactsResponse(BaseModel):
    status: str
    facts: List[Fact]
    extracted_count: int
    error_detail: str | None = None


class PrettifyRequest(BaseModel):
    raw_input_text: str


class PrettifyData(BaseModel):
    name: str
    description: str
    keywords: List[str]


class PrettifyResponse(BaseModel):
    status: str
    data: PrettifyData
    error_details: str | None = None


def _ensure(model_cls, payload):
    return payload if isinstance(payload, model_cls) else model_cls(**payload)


def _configure_model(component_id: str) -> genai.GenerativeModel:
    settings = ConfigLoader.instance().settings
    if not settings.google_api_key:
        raise EnvironmentError("GOOGLE_API_KEY is required for Gemini calls.")
    genai.configure(api_key=settings.google_api_key)
    cfg = load_model_config(component_id)
    model_id = cfg["model_id"]
    generation_config = {
        "temperature": cfg.get("temperature", 0.2),
        "top_p": cfg.get("top_p", 0.95),
        "top_k": cfg.get("top_k", 40),
        "max_output_tokens": cfg.get("max_output_tokens", 1024),
    }
    return genai.GenerativeModel(model_id, generation_config=generation_config)


def _safe_json_extract(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return None
    return None


def _extract_text_safely(resp) -> tuple[str | None, str | None]:
    """
    Return (text, finish_reason) without throwing if parts are missing.
    """
    finish_reason = None
    try:
        if hasattr(resp, "candidates") and resp.candidates:
            finish_reason = getattr(resp.candidates[0], "finish_reason", None)
        return getattr(resp, "text", None), finish_reason
    except Exception:
        return None, finish_reason


def tool_define_topic_relevance(payload: RelevanceRequest | Dict[str, Any]) -> Dict[str, Any]:
    req = _ensure(RelevanceRequest, payload)
    if os.getenv("RUN_REAL_AI") != "1":
        threshold = load_relevance_threshold("subagent_document_processor")
        return RelevanceResponse(
            status="success",
            relevance_score=max(0.9, threshold),
            reasoning="Mock relevance (RUN_REAL_AI not set).",
            error_detail=None,
        ).model_dump()
    try:
        model = _configure_model("subagent_document_processor")
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error_detail": f"LLM_AUTH_ERROR: {exc}"}

    prompt = f"""
You are a relevance scorer. Given content and a domain (name, description, keywords), return JSON: {{"score": float 0-1, "reasoning": "brief"}}.
Domain name: {req.domain_name}
Domain description: {req.domain_description}
Domain keywords: {', '.join(req.domain_keywords)}
Content:
{req.content_text}
"""
    try:
        resp = model.generate_content(prompt)
        parsed = _safe_json_extract(resp.text or "")
        score = float(parsed.get("score")) if parsed else 0.0
        reasoning = parsed.get("reasoning", "") if parsed else resp.text
        return RelevanceResponse(
            status="success",
            relevance_score=score,
            reasoning=reasoning,
            error_detail=None,
        ).model_dump()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error_detail": f"LLM_SERVICE_ERROR: {exc}"}


def tool_extract_facts_from_text(payload: ExtractFactsRequest | Dict[str, Any]) -> Dict[str, Any]:
    req = _ensure(ExtractFactsRequest, payload)
    if os.getenv("RUN_REAL_AI") != "1":
        facts = [
            Fact(fact_id="fact_mock_1", content="Mock fact 1", justification=req.relevance_justification),
            Fact(fact_id="fact_mock_2", content="Mock fact 2", justification=req.relevance_justification),
        ]
        return ExtractFactsResponse(
            status="success",
            facts=facts,
            extracted_count=len(facts),
            error_detail=None,
        ).model_dump()
    try:
        model = _configure_model("subagent_document_processor")
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error_detail": f"LLM_AUTH_ERROR: {exc}"}

    prompt = f"""
Extract atomic, verifiable facts relevant to the domain. Respond JSON: {{"facts":[{{"fact_id": "slug", "content": "fact", "justification": "why"}}]}}.
Domain: {req.domain_name}
Description: {req.domain_description}
Keywords: {', '.join(req.domain_keywords)}
Relevance justification: {req.relevance_justification}
Content:
{req.content_text}
"""
    try:
        resp = model.generate_content(prompt)
        text, finish_reason = _extract_text_safely(resp)
        if not text:
            return {
                "status": "error",
                "error_detail": f"LLM_GENERATION_FAILED: finish_reason={finish_reason}",
            }
        parsed = _safe_json_extract(text or "")
        facts_list = parsed.get("facts", []) if parsed else []
        facts = [Fact(**f) for f in facts_list]
        return ExtractFactsResponse(
            status="success",
            facts=facts,
            extracted_count=len(facts),
            error_detail=None,
        ).model_dump()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error_detail": f"LLM_GENERATION_FAILED: {exc}"}


def tool_prettify_domain_description(payload: PrettifyRequest | Dict[str, Any]) -> Dict[str, Any]:
    req = _ensure(PrettifyRequest, payload)
    if os.getenv("RUN_REAL_AI") != "1":
        data = PrettifyData(
            name="Mock Domain",
            description=req.raw_input_text,
            keywords=["mock"],
        )
        return PrettifyResponse(status="SUCCESS", data=data, error_details=None).model_dump()
    try:
        model = _configure_model("subagent_domain_lifecycle")
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error_details": f"LLM_AUTH_ERROR: {exc}"}

    prompt = f"""
Given a user's raw description of an interest area, produce JSON:
{{"name": "...", "description": "...", "keywords": ["..."]}}
Raw input:
{req.raw_input_text}
"""
    try:
        resp = model.generate_content(prompt)
        parsed = _safe_json_extract(resp.text or "")
        data = PrettifyData(
            name=parsed.get("name", "Untitled Domain"),
            description=parsed.get("description", req.raw_input_text),
            keywords=parsed.get("keywords", []),
        )
        return PrettifyResponse(status="SUCCESS", data=data, error_details=None).model_dump()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error_details": f"LLM_SERVICE_UNAVAILABLE: {exc}"}
