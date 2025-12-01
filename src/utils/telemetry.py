from __future__ import annotations

"""
Tracing utilities:
- Decorator emits SPAN_START/END logs with masked args.
- Optionally sends spans to Cloud Trace v2 when ENABLE_GCP_LOGGING=1.
"""

import functools
import os
import uuid
from typing import Any, Callable, Dict, Optional

from google.protobuf import timestamp_pb2

from .logger import get_logger, mask_pii

ENABLE_GCP_LOGGING = os.getenv("ENABLE_GCP_LOGGING") == "1"
ENABLE_LOGGING_DEBUG = os.getenv("ENABLE_LOGGING_DEBUG") == "1"
trace_client = None
trace_module = None

if ENABLE_GCP_LOGGING:
    try:
        from google.cloud import trace_v2  # type: ignore

        trace_client = trace_v2.TraceServiceClient()
        trace_module = trace_v2
    except Exception:
        trace_client = None
        trace_module = None


def trace_span(span_name: Optional[str] = None, component: Optional[str] = None) -> Callable:
    """
    Decorator to emit structured span start/end logs with masked arguments.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(component or func.__module__)
            trace_id = uuid.uuid4().hex
            masked_args = [mask_pii(str(arg)) for arg in args]
            masked_kwargs: Dict[str, Any] = {k: mask_pii(str(v)) if isinstance(v, str) else v for k, v in kwargs.items()}
            span_label = span_name or func.__name__

            span_context = None
            if ENABLE_GCP_LOGGING and trace_client and trace_module:
                try:
                    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
                    if project_id:
                        span_id = uuid.uuid4().hex[:16]
                        span_name_full = f"projects/{project_id}/traces/{trace_id}/spans/{span_id}"
                        span_context = {
                            "name": span_name_full,
                            "span_id": span_id,
                        }
                except Exception:
                    span_context = None

            logger.info(
                "SPAN_START",
                trace_id=trace_id,
                span_name=span_label,
                function_name=func.__name__,
                args=masked_args,
                kwargs=masked_kwargs,
            )
            result = func(*args, **kwargs)

            if span_context and trace_client and trace_module:
                try:
                    start_ts = timestamp_pb2.Timestamp()
                    end_ts = timestamp_pb2.Timestamp()
                    start_ts.GetCurrentTime()
                    end_ts.GetCurrentTime()
                    span = trace_module.Span(
                        name=span_context["name"],
                        span_id=span_context["span_id"],
                        display_name=trace_module.TruncatableString(value=span_label),
                        start_time=start_ts,
                        end_time=end_ts,
                    )
                    trace_client.create_span(request={"span": span})
                except Exception as exc:
                    if ENABLE_LOGGING_DEBUG:
                        import sys as _sys

                        print(f"[TRACE_ERROR] {exc}", file=_sys.stderr)

            logger.info(
                "SPAN_END",
                trace_id=trace_id,
                span_name=span_label,
                function_name=func.__name__,
            )
            return result

        return wrapper

    return decorator
