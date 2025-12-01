from __future__ import annotations

"""
Memory tool:
- Mock mode (default) returns fake memory IDs.
- Real mode (RUN_REAL_MEMORY=1) saves facts into Firestore collection.
"""

import os
import time
import uuid
from typing import Any, Dict

from google.cloud import firestore
from google.cloud.firestore import Client
from pydantic import BaseModel, Field

from src.utils.config_loader import ConfigLoader


LATENCY_SECONDS = 0.1


class SaveFactRequest(BaseModel):
    fact_text: str
    source_url: str
    user_id: str
    domain_id: str


class SaveFactData(BaseModel):
    memory_id: str


class SaveFactResponse(BaseModel):
    status: str = Field(default="success")
    data: SaveFactData
    error: str | None = None


def _ensure(model_cls, payload):
    return payload if isinstance(payload, model_cls) else model_cls(**payload)


def _firestore_client() -> Client:
    settings = ConfigLoader.instance().settings
    return firestore.Client(database=settings.firestore_database or "(default)")


def tool_save_fact_to_memory(payload: SaveFactRequest | Dict[str, Any]) -> Dict[str, Any]:
    req = _ensure(SaveFactRequest, payload)

    # Mock path unless explicitly told to hit real persistence.
    if os.getenv("RUN_REAL_MEMORY") != "1":
        time.sleep(LATENCY_SECONDS)
        data = SaveFactData(memory_id=f"mem_{uuid.uuid4().hex[:8]}")
        return SaveFactResponse(status="success", data=data, error=None).model_dump()

    # "Real" path: persist to Firestore memory_facts collection (serves as durable store).
    try:
        client = _firestore_client()
        collection = os.getenv("MEMORY_COLLECTION_NAME", "memory_facts")
        doc_ref = client.collection(collection).document()
        doc_ref.set(
            {
                "fact_text": req.fact_text,
                "source_url": req.source_url,
                "user_id": req.user_id,
                "domain_id": req.domain_id,
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
        return SaveFactResponse(status="success", data=SaveFactData(memory_id=doc_ref.id), error=None).model_dump()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"MEMORY_WRITE_ERROR: {exc}"}
