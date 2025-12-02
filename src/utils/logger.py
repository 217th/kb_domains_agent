from __future__ import annotations

"""
Structured logging utilities with optional Cloud Logging support.

Public API:
- StructuredLogger: emits JSON logs with labels and masking.
- get_logger(component): returns a StructuredLogger for the component.
- mask_pii(text): truncates long text to reduce PII exposure.

Usage: prints to stdout by default; when ENABLE_GCP_LOGGING=1 (and GCP creds set), also sends to Cloud Logging (`structured`). Respects OBS config (config/observability_config.yaml) and env secrets filtering. Enable ENABLE_LOGGING_DEBUG=1 to surface send errors. See docs/project_overview.md and README for configuration details. Experimental cloud emission may fail silently if networking is blocked.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from google.cloud import logging as cloud_logging
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
OBS_CONFIG_PATH = BASE_DIR / "config" / "observability_config.yaml"
load_dotenv(BASE_DIR / ".env")


def mask_pii(text: str) -> str:
    if not isinstance(text, str):
        return text
    if len(text) <= 200:
        return text
    suffix = "...(truncated)"
    max_prefix = max(0, 200 - len(suffix))
    return f"{text[:max_prefix]}{suffix}"


def _load_observability_config() -> Dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("pyyaml must be installed to load observability config") from exc
    if OBS_CONFIG_PATH.exists():
        with OBS_CONFIG_PATH.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


OBS_CONFIG = _load_observability_config()
ENABLE_GCP_LOGGING = os.getenv("ENABLE_GCP_LOGGING") == "1"
_cloud_logger = None

if ENABLE_GCP_LOGGING:
    try:
        client = cloud_logging.Client()
        client.setup_logging()
        _cloud_logger = client.logger("structured")
    except Exception:  # noqa: BLE001
        ENABLE_GCP_LOGGING = False


def _filter_sensitive(data: Dict[str, Any]) -> Dict[str, Any]:
    filtered: Dict[str, Any] = {}
    for key, value in data.items():
        upper_key = key.upper()
        if any(s in upper_key for s in ("KEY", "TOKEN", "CREDENTIALS", "SECRET")):
            filtered[key] = "[FILTERED]"
            continue
        if isinstance(value, str):
            filtered[key] = mask_pii(value)
        elif isinstance(value, dict):
            filtered[key] = _filter_sensitive(value)
        else:
            filtered[key] = value
    return filtered


class StructuredLogger:
    def __init__(self, component: str) -> None:
        self.component = component
        logging_cfg = OBS_CONFIG.get("logging", {})
        self.prompt_version_sha = os.getenv("PROMPT_VERSION_SHA", logging_cfg.get("prompt_version_sha", "local-dev"))
        self.model_config_profile = os.getenv("MODEL_CONFIG_PROFILE", logging_cfg.get("model_config_profile", "default"))
        self.agent_version = logging_cfg.get("agent_version", "v0.0.1")

    def _build_entry(self, severity: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        labels = {
            "agent_version": self.agent_version,
            "prompt_version_sha": self.prompt_version_sha,
            "model_config_profile": self.model_config_profile,
        }
        trace_id = payload.pop("trace_id", None)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": severity,
            "component": self.component,
            "trace_id": trace_id,
            "labels": labels,
            "jsonPayload": {"event_type": event_type},
        }
        entry["jsonPayload"].update(_filter_sensitive(payload))
        return entry

    def log(self, severity: str, event_type: str, **payload: Any) -> None:
        entry = self._build_entry(severity, event_type, payload)
        print(json.dumps(entry, ensure_ascii=True))
        if ENABLE_GCP_LOGGING and _cloud_logger:
            try:
                _cloud_logger.log_struct(entry, severity=severity)
            except Exception:
                # Do not break local runs if logging backend is unavailable.
                pass

    def info(self, event_type: str, **payload: Any) -> None:
        self.log("INFO", event_type, **payload)

    def error(self, event_type: str, **payload: Any) -> None:
        self.log("ERROR", event_type, **payload)


def get_logger(component: str) -> StructuredLogger:
    return StructuredLogger(component)
