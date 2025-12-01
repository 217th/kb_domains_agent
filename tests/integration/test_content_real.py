import os
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

REAL_CONTENT = os.getenv("RUN_REAL_CONTENT_TESTS") == "1"


@pytest.mark.skipif(not REAL_CONTENT, reason="Set RUN_REAL_CONTENT_TESTS=1 to run real content fetches")
def test_real_ordinary_page():
    from src.tools.content import tool_process_ordinary_page

    result = tool_process_ordinary_page({"url": "https://example.com"})
    assert result["status"] == "success"
    assert "Example Domain" in result["content"]


@pytest.mark.skipif(not REAL_CONTENT, reason="Set RUN_REAL_CONTENT_TESTS=1 to run real content fetches")
def test_real_pdf_processing():
    from src.tools.content import tool_process_pdf_link

    result = tool_process_pdf_link({"url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"})
    assert result["status"] == "success"
    assert result["metadata"]["page_count"] >= 1
    assert "Dummy PDF" in result["content"]
