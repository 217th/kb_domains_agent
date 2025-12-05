---
id: ARCH-infra-observability
title: "Infrastructure: Observability"
type: component
layer: infrastructure
owner: @team-platform
version: v1
status: current
created: 2025-12-02
updated: 2025-12-02
tags: [logging, tracing, gcp]
depends_on: []
referenced_by: []
---
## Context
Provides structured logging and distributed tracing capabilities, optionally integrating with Google Cloud Logging and Cloud Trace.

## Structure
*   **Files:**
    *   `src/utils/logger.py`: Structured JSON logger.
    *   `src/utils/telemetry.py`: Tracing decorators.
    *   `config/observability_config.yaml`: Logging settings.

## Behavior
*   **Structured Logging:** Outputs JSON logs with severity, component, and trace IDs. Masks PII and secrets.
*   **Tracing:** `trace_span` decorator wraps functions to emit start/end logs and send spans to GCP Trace (if enabled).
*   **PII Masking:** Automatically truncates long strings and filters sensitive keys (e.g., "KEY", "TOKEN").
*   **GCP Integration:** Controlled via `ENABLE_GCP_LOGGING` env var.

## Evolution
### Historical
*   v1: Implemented structured logging and decorator-based tracing with PII masking.
