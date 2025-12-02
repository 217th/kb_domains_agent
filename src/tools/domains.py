from __future__ import annotations

"""
Domain tools:
- Fetch/toggle domains from Firestore.
- Generate/export snapshots (mocked).
- Prettify domain description (delegates to AI).

Public API:
- tool_fetch_user_knowledge_domains(payload): list domains with filters.
- tool_toggle_domain_status(payload): flip active/inactive for a domain.
- tool_generate_domain_snapshot(payload): mocked summary.
- tool_export_detailed_domain_snapshot(payload): mocked export link.
- tool_prettify_domain_description(payload): delegates to AI prettify.

Usage: Firestore-backed reads/writes; requires GCP creds/project/FIRESTORE_DATABASE. Prettify relies on ai_analysis (Gemini) or mock via RUN_REAL_AI flag. Snapshot/export remain mocked. See docs/tool_* JSON specs and README for flags (`RUN_REAL_DOMAINS` controls save in lifecycle agent, not here).
"""

from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.cloud.firestore import Client
from pydantic import BaseModel, Field, field_validator

from src.utils.config_loader import ConfigLoader
from src.tools import ai_analysis


def _client() -> Client:
    settings = ConfigLoader.instance().settings
    return firestore.Client(database=settings.firestore_database or "(default)")


class FetchDomainsRequest(BaseModel):
    user_id: str
    status_filter: str = Field(default="ALL")
    view_mode: str = Field(default="BRIEF")

    @field_validator("status_filter")
    @classmethod
    def validate_status_filter(cls, v: str) -> str:
        allowed = {"ALL", "ACTIVE", "INACTIVE"}
        if v not in allowed:
            raise ValueError("status_filter must be one of ALL, ACTIVE, INACTIVE")
        return v

    @field_validator("view_mode")
    @classmethod
    def validate_view_mode(cls, v: str) -> str:
        allowed = {"BRIEF", "DETAILED"}
        if v not in allowed:
            raise ValueError("view_mode must be one of BRIEF, DETAILED")
        return v


class Domain(BaseModel):
    domain_id: str
    name: str
    status: str
    domain_description: Optional[str] = None
    domain_keywords: Optional[List[str]] = None


class FetchDomainsResponse(BaseModel):
    status: str
    data: List[Domain]


class ToggleDomainRequest(BaseModel):
    user_id: str
    domain_id: str


class ToggleDomainData(BaseModel):
    domain_id: str
    previous_status: str
    new_status: str


class ToggleDomainResponse(BaseModel):
    status: str = "success"
    data: ToggleDomainData


class GenerateSnapshotRequest(BaseModel):
    user_id: str
    domain_id: str


class SnapshotMeta(BaseModel):
    fact_count: int
    total_char_length: int
    source_count: int


class SnapshotData(BaseModel):
    domain_id: str
    domain_name: str
    super_summary: str
    extended_summary: str
    meta_info: SnapshotMeta


class GenerateSnapshotResponse(BaseModel):
    status: str = "success"
    data: SnapshotData


class ExportSnapshotRequest(BaseModel):
    user_id: str
    domain_id: str


class ExportSnapshotData(BaseModel):
    domain_id: str
    download_url: str
    file_size_bytes: int
    file_format: str = "markdown"


class ExportSnapshotResponse(BaseModel):
    status: str
    data: ExportSnapshotData


class PrettifyDomainRequest(BaseModel):
    raw_input_text: str

    @field_validator("raw_input_text")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("raw_input_text cannot be empty")
        return v


def _ensure(model_cls, payload):
    return payload if isinstance(payload, model_cls) else model_cls(**payload)


def _doc_to_domain(doc) -> Domain:
    data = doc.to_dict() or {}
    return Domain(
        domain_id=doc.id,
        name=data.get("name", ""),
        status=data.get("status", "inactive"),
        domain_description=data.get("domain_description"),
        domain_keywords=data.get("domain_keywords"),
    )


def tool_fetch_user_knowledge_domains(payload: FetchDomainsRequest | Dict[str, Any]) -> Dict[str, Any]:
    req = _ensure(FetchDomainsRequest, payload)
    client = _client()
    try:
        query = client.collection("domains").where("user_id", "==", req.user_id)
        if req.status_filter != "ALL":
            query = query.where("status", "==", req.status_filter.lower())
        docs = list(query.stream())
        if not docs:
            return FetchDomainsResponse(status="empty", data=[]).model_dump()
        domains = [_doc_to_domain(doc) for doc in docs]
        if req.view_mode == "BRIEF":
            domains = [
                Domain(domain_id=d.domain_id, name=d.name, status=d.status)  # type: ignore[arg-type]
                for d in domains
            ]
        return FetchDomainsResponse(status="success", data=domains).model_dump()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"FIRESTORE_UNAVAILABLE: {exc}"}


def tool_toggle_domain_status(payload: ToggleDomainRequest | Dict[str, Any]) -> Dict[str, Any]:
    req = _ensure(ToggleDomainRequest, payload)
    client = _client()
    doc_ref = client.collection("domains").document(req.domain_id)
    try:
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return {"status": "error", "error": "DOMAIN_NOT_FOUND"}
        data = snapshot.to_dict() or {}
        if data.get("user_id") != req.user_id:
            return {"status": "error", "error": "PERMISSION_DENIED"}
        previous = data.get("status", "inactive")
        new_status = "inactive" if previous == "active" else "active"
        doc_ref.update({"status": new_status})
        return ToggleDomainResponse(
            status="success",
            data=ToggleDomainData(domain_id=req.domain_id, previous_status=previous, new_status=new_status),
        ).model_dump()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"FIRESTORE_UNAVAILABLE: {exc}"}


def tool_generate_domain_snapshot(payload: GenerateSnapshotRequest | Dict[str, Any]) -> Dict[str, Any]:
    """
    Snapshot still mocked; Firestore lookup for domain name.
    """
    req = _ensure(GenerateSnapshotRequest, payload)
    client = _client()
    doc_ref = client.collection("domains").document(req.domain_id)
    domain_name = "Domain"
    try:
        snap = doc_ref.get()
        if snap.exists:
            domain_name = snap.to_dict().get("name", domain_name)
    except Exception:
        pass
    data = SnapshotData(
        domain_id=req.domain_id,
        domain_name=domain_name,
        super_summary="AI research highlights in ~20 words.",
        extended_summary="A concise summary of recent AI papers and advancements, focused on model scaling and efficiency.",
        meta_info=SnapshotMeta(fact_count=12, total_char_length=2400, source_count=5),
    )
    return GenerateSnapshotResponse(status="success", data=data).model_dump()


def tool_export_detailed_domain_snapshot(payload: ExportSnapshotRequest | Dict[str, Any]) -> Dict[str, Any]:
    """
    Still mocked; would require storage + memory bank in later phases.
    """
    req = _ensure(ExportSnapshotRequest, payload)
    data = ExportSnapshotData(
        domain_id=req.domain_id,
        download_url="https://mock-bucket.s3.mock/exports/domain_report.md",
        file_size_bytes=2048,
        file_format="markdown",
    )
    return ExportSnapshotResponse(status="success", data=data).model_dump()


def tool_prettify_domain_description(payload: PrettifyDomainRequest | Dict[str, Any]) -> Dict[str, Any]:
    # Delegate to AI analysis module for real implementation.
    return ai_analysis.tool_prettify_domain_description(payload)
