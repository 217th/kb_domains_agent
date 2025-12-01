from __future__ import annotations

"""
Content tools (real):
- Ordinary page scraping via requests + BeautifulSoup.
- PDF download and text extraction via pypdf.
- YouTube transcript fetch via youtube-transcript-api.
"""

import re
from io import BytesIO
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi

USER_AGENT = "Mozilla/5.0 (compatible; ADKMock/1.0; +https://example.com)"


class UrlRequest(BaseModel):
    url: HttpUrl


class OrdinaryPageResponse(BaseModel):
    status: str
    content: str
    page_title: str
    error_detail: str | None = None


class PdfMetadata(BaseModel):
    page_count: int


class PdfResponse(BaseModel):
    status: str
    content: str
    metadata: PdfMetadata
    error_detail: str | None = None


class YoutubeResponse(BaseModel):
    status: str
    content: str
    video_title: str
    error_detail: str | None = None


def _ensure(model_cls, payload):
    return payload if isinstance(payload, model_cls) else model_cls(**payload)


def _http_get(url: str, stream: bool = False) -> requests.Response:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10, stream=stream)
    resp.raise_for_status()
    return resp


def _clean_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    return text, title


def tool_process_ordinary_page(payload: UrlRequest | Dict[str, Any]) -> Dict[str, Any]:
    req = _ensure(UrlRequest, payload)
    try:
        resp = _http_get(str(req.url))
    except requests.exceptions.Timeout:
        return OrdinaryPageResponse(status="error", content="", page_title="", error_detail="TIMEOUT").model_dump()
    except requests.HTTPError as exc:
        code = exc.response.status_code if exc.response else "UNKNOWN"
        return OrdinaryPageResponse(status="error", content="", page_title="", error_detail=f"HTTP_ERROR_{code}").model_dump()
    except Exception as exc:  # noqa: BLE001
        return OrdinaryPageResponse(status="error", content="", page_title="", error_detail=str(exc)).model_dump()

    text, title = _clean_html(resp.text)
    if not text:
        return OrdinaryPageResponse(status="error", content="", page_title=title, error_detail="EMPTY_CONTENT").model_dump()
    return OrdinaryPageResponse(status="success", content=text, page_title=title, error_detail=None).model_dump()


def tool_process_pdf_link(payload: UrlRequest | Dict[str, Any]) -> Dict[str, Any]:
    req = _ensure(UrlRequest, payload)
    try:
        resp = _http_get(str(req.url), stream=True)
        content_bytes = resp.content
        reader = PdfReader(BytesIO(content_bytes))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(text_parts).strip()
        meta = PdfMetadata(page_count=len(reader.pages))
        if not text:
            return PdfResponse(status="error", content="", metadata=meta, error_detail="EMPTY_CONTENT").model_dump()
        return PdfResponse(status="success", content=text, metadata=meta, error_detail=None).model_dump()
    except requests.exceptions.Timeout:
        return PdfResponse(status="error", content="", metadata=PdfMetadata(page_count=0), error_detail="DOWNLOAD_FAILED").model_dump()
    except requests.HTTPError as exc:
        code = exc.response.status_code if exc.response else "UNKNOWN"
        return PdfResponse(status="error", content="", metadata=PdfMetadata(page_count=0), error_detail=f"HTTP_ERROR_{code}").model_dump()
    except Exception as exc:  # noqa: BLE001
        return PdfResponse(status="error", content="", metadata=PdfMetadata(page_count=0), error_detail=f"PARSING_ERROR: {exc}").model_dump()


def _extract_youtube_id(url: str) -> str | None:
    parsed = urlparse(url)
    if "youtube" in parsed.netloc or "youtu.be" in parsed.netloc:
        if parsed.netloc in {"youtu.be"}:
            return parsed.path.lstrip("/")
        qs = parse_qs(parsed.query)
        return qs.get("v", [None])[0]
    return None


def tool_process_youtube_link(payload: UrlRequest | Dict[str, Any]) -> Dict[str, Any]:
    req = _ensure(UrlRequest, payload)
    video_id = _extract_youtube_id(str(req.url))
    if not video_id:
        return YoutubeResponse(status="error", content="", video_title="", error_detail="INVALID_URL").model_dump()
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(chunk["text"] for chunk in transcript if chunk.get("text"))
        title = f"YouTube Video {video_id}"
        if not text:
            return YoutubeResponse(status="error", content="", video_title=title, error_detail="NO_TRANSCRIPT_FOUND").model_dump()
        return YoutubeResponse(status="success", content=text, video_title=title, error_detail=None).model_dump()
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        if "No transcripts" in msg:
            detail = "NO_TRANSCRIPT_FOUND"
        else:
            detail = "VIDEO_UNAVAILABLE"
        return YoutubeResponse(status="error", content="", video_title="", error_detail=detail).model_dump()
