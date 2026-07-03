# -*- coding: utf-8 -*-
"""OpenTelemetry integration — optional tracing for LLM / tool / task / plaza.

Usage:
    from monitoring.tracing import init_tracing, get_tracer

    # At startup (main.py):
    init_tracing(app)  # instruments FastAPI if OTel is available

    # In any module:
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("key", "value")
        ...

If opentelemetry packages are not installed, all functions are no-ops.
Enable via env: AG_OTEL_ENABLED=1
Configure endpoint: AG_OTEL_ENDPOINT=http://localhost:4317
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Optional

logger = logging.getLogger("tracing")

_ENABLED = os.getenv("AG_OTEL_ENABLED", "").strip() in ("1", "true", "yes")
_ENDPOINT = os.getenv("AG_OTEL_ENDPOINT", "http://localhost:4317")
_SERVICE_NAME = os.getenv("AG_OTEL_SERVICE_NAME", "agentsgroup2026")

# Will be set to real tracer provider if OTel is available
_tracer_provider: Any = None
_initialized = False


class _NoOpSpan:
    """Stub span when OTel is not available."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, *args: Any, **kwargs: Any) -> None:
        pass

    def record_exception(self, exc: BaseException) -> None:
        pass

    def end(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _NoOpTracer:
    """Stub tracer when OTel is not available."""

    @contextmanager
    def start_as_current_span(self, name: str, **kwargs: Any):
        yield _NoOpSpan()

    def start_span(self, name: str, **kwargs: Any) -> _NoOpSpan:
        return _NoOpSpan()


_noop_tracer = _NoOpTracer()


def init_tracing(app: Any = None) -> bool:
    """Initialize OpenTelemetry tracing.

    Returns True if OTel was successfully initialized, False otherwise.
    """
    global _tracer_provider, _initialized

    if _initialized:
        return _tracer_provider is not None

    _initialized = True

    if not _ENABLED:
        logger.info("OTel tracing disabled (set AG_OTEL_ENABLED=1 to enable)")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        resource = Resource.create({"service.name": _SERVICE_NAME})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=_ENDPOINT)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _tracer_provider = provider

        # Instrument FastAPI if app provided
        if app is not None:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
                FastAPIInstrumentor.instrument_app(app)
                logger.info("FastAPI instrumented with OTel")
            except ImportError:
                logger.warning("opentelemetry-instrumentation-fastapi not installed")

        logger.info("OTel tracing initialized → %s", _ENDPOINT)
        return True

    except ImportError:
        logger.info("OpenTelemetry packages not installed — tracing disabled")
        return False
    except Exception as e:
        logger.error("Failed to initialize OTel: %s", e)
        return False


def get_tracer(name: str = __name__) -> Any:
    """Get a tracer instance. Returns NoOp if OTel is not available."""
    if _tracer_provider is not None:
        try:
            from opentelemetry import trace
            return trace.get_tracer(name)
        except ImportError:
            pass
    return _noop_tracer


def trace_llm_call(model: str, prompt_tokens: int = 0, completion_tokens: int = 0):
    """Decorator/context-manager to trace LLM API calls."""
    tracer = get_tracer("llm")

    @contextmanager
    def _ctx():
        with tracer.start_as_current_span("llm.call") as span:
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.prompt_tokens", prompt_tokens)
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                raise
            finally:
                if completion_tokens:
                    span.set_attribute("llm.completion_tokens", completion_tokens)

    return _ctx()


def trace_tool_execution(tool_name: str, agent_id: str = ""):
    """Context-manager to trace tool executions."""
    tracer = get_tracer("tool")

    @contextmanager
    def _ctx():
        with tracer.start_as_current_span("tool.execute") as span:
            span.set_attribute("tool.name", tool_name)
            if agent_id:
                span.set_attribute("agent.id", agent_id)
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                raise

    return _ctx()


def trace_plaza_discussion(plaza_id: str, discussion_id: str, topic: str = ""):
    """Context-manager to trace plaza discussions."""
    tracer = get_tracer("plaza")

    @contextmanager
    def _ctx():
        with tracer.start_as_current_span("plaza.discussion") as span:
            span.set_attribute("plaza.id", plaza_id)
            span.set_attribute("plaza.discussion_id", discussion_id)
            if topic:
                span.set_attribute("plaza.topic", topic)
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                raise

    return _ctx()
