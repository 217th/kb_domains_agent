import json
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))
os.environ.pop("ENABLE_GCP_LOGGING", None)


def test_trace_span_logs_and_masks(capsys):
    from src.utils.telemetry import trace_span

    @trace_span(span_name="llm_fact_extraction", component="subagent_document_processor")
    def sample_func(fact_text: str) -> str:
        return fact_text[::-1]

    long_text = "x" * 205
    result = sample_func(long_text)
    assert result == long_text[::-1]

    logs = capsys.readouterr().out.strip().splitlines()
    assert len(logs) == 2
    start_entry = json.loads(logs[0])
    assert start_entry["severity"] == "INFO"
    assert start_entry["labels"]["prompt_version_sha"]
    masked_arg = start_entry["jsonPayload"]["args"][0]
    assert masked_arg.endswith("...(truncated)")
    assert len(masked_arg) <= 200
    assert "http" not in masked_arg  # basic sanity to ensure masking triggers


def test_trace_span_includes_trace_and_span_name(capsys):
    from src.utils.telemetry import trace_span

    @trace_span(span_name="demo_span", component="demo_component")
    def foo(x):
        return x

    foo("sensitive_data_should_be_masked_" + "y" * 220)
    logs = capsys.readouterr().out.strip().splitlines()
    assert len(logs) == 2
    start = json.loads(logs[0])
    end = json.loads(logs[1])
    assert start["jsonPayload"]["span_name"] == "demo_span"
    assert start["trace_id"]
    assert start["trace_id"] == end["trace_id"]
    masked_arg = start["jsonPayload"]["args"][0]
    assert masked_arg.endswith("...(truncated)")
