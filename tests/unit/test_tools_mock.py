import sys
from pathlib import Path

import pytest


class FakeDocRef:
    def __init__(self, doc_id: str, data=None):
        self.id = doc_id
        self._data = data or {}
        self.exists = bool(data)

    def set(self, data):
        self._data = data
        self.exists = True

    def update(self, updates):
        self._data.update(updates)

    def get(self):
        return self

    def to_dict(self):
        return self._data


class FakeCollection:
    def __init__(self, initial=None):
        initial = initial or {}
        self.docs = {k: FakeDocRef(k, v) for k, v in initial.items()}

    def document(self, doc_id=None):
        doc_id = doc_id or f"doc_{len(self.docs)+1}"
        if doc_id not in self.docs:
            self.docs[doc_id] = FakeDocRef(doc_id, {})
        return self.docs[doc_id]

    def where(self, *_, **__):
        return self

    def limit(self, *_):
        return self

    def stream(self):
        return iter(self.docs.values())


class FakeClient:
    def __init__(self):
        self.collections = {
            "users": FakeCollection({}),
            "domains": FakeCollection(
                {
                    "dom_ai": {
                        "user_id": "user_1",
                        "name": "AI Research",
                        "status": "active",
                        "domain_description": "Desc",
                        "domain_keywords": ["AI"],
                    }
                }
            ),
        }

    def collection(self, name: str):
        return self.collections[name]


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))


def test_tool_auth_user_returns_id(monkeypatch):
    from src.tools import auth

    fake_client = FakeClient()
    monkeypatch.setattr(auth, "_get_client", lambda: fake_client, raising=False)

    result = auth.tool_auth_user({"username": "Alice"})
    assert result["status"] == "success"
    assert isinstance(result["data"]["user_id"], str)
    assert result["data"]["user_id"]


def test_fetch_domains_detailed_view(monkeypatch):
    from src.tools import domains

    fake_client = FakeClient()
    monkeypatch.setattr(domains, "_client", lambda: fake_client, raising=False)

    result = domains.tool_fetch_user_knowledge_domains({"user_id": "user_1", "view_mode": "DETAILED"})
    assert result["status"] == "success"
    assert len(result["data"]) >= 1
    first = result["data"][0]
    assert "domain_description" in first and first["domain_description"]
    assert isinstance(first.get("domain_keywords"), list)


def test_toggle_domain_status(monkeypatch):
    from src.tools import domains

    fake_client = FakeClient()
    monkeypatch.setattr(domains, "_client", lambda: fake_client, raising=False)

    result = domains.tool_toggle_domain_status({"user_id": "user_1", "domain_id": "dom_ai"})
    assert result["status"] == "success"
    assert result["data"]["previous_status"] != result["data"]["new_status"]


def test_prettify_domain_description(monkeypatch):
    from src.tools import ai_analysis
    from src.tools.domains import tool_prettify_domain_description

    def fake_prettify(payload):
        return {
            "status": "SUCCESS",
            "data": {"name": "Mock", "description": "Desc", "keywords": ["k1"]},
            "error_details": None,
        }

    monkeypatch.setattr(ai_analysis, "tool_prettify_domain_description", fake_prettify, raising=False)

    result = tool_prettify_domain_description({"raw_input_text": "Track AI topics"})
    assert result["status"] == "SUCCESS"
    assert result["data"]["keywords"]


def test_generate_and_export_snapshot(monkeypatch):
    from src.tools import domains

    fake_client = FakeClient()
    monkeypatch.setattr(domains, "_client", lambda: fake_client, raising=False)

    snapshot = domains.tool_generate_domain_snapshot({"user_id": "user_1", "domain_id": "dom_ai"})
    assert snapshot["status"] == "success"
    assert snapshot["data"]["meta_info"]["fact_count"] >= 1

    export = domains.tool_export_detailed_domain_snapshot({"user_id": "user_1", "domain_id": "dom_ai"})
    assert export["status"] == "success"
    assert export["data"]["download_url"].startswith("https://")


def test_content_tools(monkeypatch):
    import types
    from src.tools import content

    class FakeResp:
        def __init__(self, text="", content=b""):
            self.text = text
            self.content = content
            self.status_code = 200

        def raise_for_status(self):
            return None

    class FakeRequests(types.SimpleNamespace):
        @staticmethod
        def get(url, headers=None, timeout=10, stream=False):
            if url.endswith(".pdf"):
                return FakeResp(content=b"pdf-bytes")
            return FakeResp(text="<html><title>Example</title><body><p>Mocked readable article content about AI innovations.</p></body></html>")

    class FakePage:
        @staticmethod
        def extract_text():
            return "PDF page text"

    class FakePdfReader:
        def __init__(self, _):
            self.pages = [FakePage(), FakePage()]

    class FakeYT:
        @staticmethod
        def get_transcript(_video_id):
            return [{"text": "Mock transcript of a YouTube talk on AI safety."}]

    monkeypatch.setattr(content, "requests", FakeRequests)
    monkeypatch.setattr(content, "PdfReader", FakePdfReader)
    monkeypatch.setattr(content, "YouTubeTranscriptApi", FakeYT)

    page = content.tool_process_ordinary_page({"url": "https://example.com"})
    assert page["status"] == "success"
    assert "Mocked readable article" in page["content"]

    pdf = content.tool_process_pdf_link({"url": "https://example.com/sample.pdf"})
    assert pdf["status"] == "success"
    assert pdf["metadata"]["page_count"] == 2

    yt = content.tool_process_youtube_link({"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert yt["status"] == "success"
    assert "Mock transcript" in yt["content"]


def test_ai_analysis_tools_use_threshold():
    from src.tools import ai_analysis
    from src.utils.config_loader import load_relevance_threshold

    class FakeModel:
        def __init__(self, _id=None, generation_config=None):
            self._id = _id
            self._cfg = generation_config

        def generate_content(self, prompt):
            class Resp:
                text = '{"score": 0.9, "reasoning": "relevant", "facts": [{"fact_id": "f1", "content": "c1", "justification": "j1"}, {"fact_id": "f2", "content": "c2", "justification": "j2"}]}'

            return Resp()

    ai_analysis.genai.GenerativeModel = FakeModel  # type: ignore[attr-defined]
    threshold = load_relevance_threshold("subagent_document_processor")
    relevance = ai_analysis.tool_define_topic_relevance(
        {
            "content_text": "AI breakthroughs",
            "domain_name": "AI Research",
            "domain_description": "AI studies",
            "domain_keywords": ["AI", "ML"],
        }
    )
    assert relevance["status"] == "success"
    assert relevance["relevance_score"] >= threshold
    facts = ai_analysis.tool_extract_facts_from_text(
        {
            "content_text": "AI breakthroughs",
            "domain_name": "AI Research",
            "domain_description": "AI studies",
            "domain_keywords": ["AI", "ML"],
            "relevance_justification": relevance["reasoning"],
        }
    )
    assert facts["status"] == "success"
    assert len(facts["facts"]) == facts["extracted_count"] == 2


def test_save_fact_to_memory():
    import os
    from src.tools.memory import tool_save_fact_to_memory

    os.environ.pop("RUN_REAL_MEMORY", None)
    result = tool_save_fact_to_memory(
        {
            "fact_text": "Transformers scale with data.",
            "source_url": "https://example.com",
            "user_id": "user_1",
            "domain_id": "dom_ai",
        }
    )
    assert result["status"] == "success"
    assert result["data"]["memory_id"].startswith("mem_")
