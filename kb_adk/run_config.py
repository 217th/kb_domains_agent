"""RunConfig profiles mapping env flags to ADK RunConfig.

Profiles:
- dev: mocks by default (RUN_REAL_AI=0, RUN_REAL_MEMORY=0), max_llm_calls=100.
- prod: real services (RUN_REAL_AI=1, RUN_REAL_MEMORY=1), tracing enabled via custom_metadata flag.
"""

from __future__ import annotations

import os
from google.adk.runners import RunConfig
from google.adk.agents.run_config import StreamingMode


def from_env(profile: str | None = None) -> RunConfig:
    profile = (profile or os.getenv("ADK_RUN_PROFILE", "dev")).lower()
    run_real_ai = os.getenv("RUN_REAL_AI", "0") == "1"
    run_real_mem = os.getenv("RUN_REAL_MEMORY", "0") == "1"
    enable_trace = os.getenv("ENABLE_GCP_LOGGING", "0") == "1"

    common = dict(
        streaming_mode=StreamingMode.NONE,
        max_llm_calls=200 if profile == "prod" else 100,
        custom_metadata={
            "profile": profile,
            "run_real_ai": run_real_ai,
            "run_real_memory": run_real_mem,
            "trace": enable_trace,
        },
    )

    return RunConfig(**common)
