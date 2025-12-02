from __future__ import annotations

"""
FastAPI harness exposing agent_root and subagents for HTTP access.
Use ./adk web to run; designed primarily for local/mock flows.

Public API:
- /agent-root (POST): runs agent_root.
- /subagent-domain-lifecycle (POST): runs domain lifecycle subagent.
- /subagent-document-processor (POST): runs doc processor subagent.
- /docs/status (GET): lists endpoints.

Usage: `./adk web` starts uvicorn server. Honors environment flags for AI/memory/domains/logging. Not a full ADK web UI; meant for local API testing. See README and docs/project_overview.md.
"""

from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from src.agents.agent_root import run_agent_root
from src.agents.subagent_document_processor import run_subagent_document_processor
from src.agents.subagent_domain_lifecycle import run_subagent_domain_lifecycle

app = FastAPI(title="ADK Mock Harness", version="0.1.0")


class AgentRootRequest(BaseModel):
    user_message: str
    session_user_id: Optional[str] = None


class DomainLifecycleRequest(BaseModel):
    operation_type: str
    user_id: str
    user_input: str
    confirmation_status: bool = False
    domain_id: Optional[str] = None


class DocumentProcessorRequest(BaseModel):
    user_id: str
    raw_text: Optional[str] = None
    selected_fact_ids: Optional[list[str]] = None
    facts_payload: Optional[list[dict]] = None


@app.get("/")
def read_root():
    return {
        "message": "Mock ADK harness ready.",
        "endpoints": ["/agent-root", "/subagent-domain-lifecycle", "/subagent-document-processor"],
    }


@app.post("/agent-root")
def agent_root(req: AgentRootRequest):
    return run_agent_root(req.user_message, session_user_id=req.session_user_id)


@app.post("/subagent-domain-lifecycle")
def subagent_domain_lifecycle(req: DomainLifecycleRequest):
    return run_subagent_domain_lifecycle(req.model_dump())


@app.post("/subagent-document-processor")
def subagent_document_processor(req: DocumentProcessorRequest):
    return run_subagent_document_processor(req.model_dump())


@app.get("/docs/status")
def docs_status():
    return {
        "message": "Mock ADK harness endpoints",
        "agent_root": "/agent-root",
        "subagent_domain_lifecycle": "/subagent-domain-lifecycle",
        "subagent_document_processor": "/subagent-document-processor",
    }
