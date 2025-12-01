import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))


def test_prompts_and_model_config_loads():
    from src.utils.config_loader import (
        ConfigLoader,
        load_model_config,
        load_prompts,
        load_relevance_threshold,
    )

    loader = ConfigLoader.instance()
    prompts = load_prompts()
    assert "agent_root" in prompts
    assert "Knowledge System Orchestrator" in prompts["agent_root"]

    model_cfg = load_model_config("agent_root")
    assert model_cfg["temperature"] == 0.0
    assert "gemini" in model_cfg["model_id"]

    threshold = load_relevance_threshold("subagent_document_processor")
    assert pytest.approx(threshold) == 0.7
