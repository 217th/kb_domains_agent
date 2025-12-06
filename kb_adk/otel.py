"""Lightweight OpenTelemetry bootstrap for ADK runs.

If `ENABLE_GCP_LOGGING=1` and `GOOGLE_CLOUD_PROJECT` are set, configures the
Cloud Trace exporter and attaches a service/resource. Safe to import multiple
times (idempotent based on tracer provider class name).
"""

from __future__ import annotations

import os
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing_if_enabled() -> None:
    if os.getenv("ENABLE_GCP_LOGGING", "0") != "1":
        return
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        return

    current = trace.get_tracer_provider()
    if isinstance(current, TracerProvider):
        # Already configured (ADK or previous call)
        return

    resource = Resource.create({"service.name": "kb_adk", "service.version": "0.0.1"})
    provider = TracerProvider(resource=resource)
    exporter = CloudTraceSpanExporter(project_id=project)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


# Run on import for convenience
setup_tracing_if_enabled()

