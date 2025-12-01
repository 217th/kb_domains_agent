import os
import sys
import uuid
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))


RUN_REAL_MEMORY = os.getenv("RUN_REAL_MEMORY") == "1"


@pytest.mark.skipif(not RUN_REAL_MEMORY, reason="Set RUN_REAL_MEMORY=1 to run real memory integration")
def test_save_fact_to_memory_real():
    from src.tools.memory import tool_save_fact_to_memory

    fact_id = f"fact_{uuid.uuid4().hex[:6]}"
    res = tool_save_fact_to_memory(
        {
            "fact_text": f"Test fact {fact_id}",
            "source_url": "https://example.com",
            "user_id": "user_integration",
            "domain_id": "dom_integration",
        }
    )
    assert res["status"] == "success"
    assert res["data"]["memory_id"]
