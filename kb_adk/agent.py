"""ADK wrapper that adapts existing business logic to the Runner/event model.

- Uses google-adk Runner expectations: exposes `root_agent` (BaseAgent).
- Delegates to legacy logic in `src.agents.agent_root` and sub-agents while
  mapping ADK session state via EventActions.state_delta.
- Default model config remains external; tools keep using Gemini 2.5 Flash via
  existing prompts/config loader.
"""

from __future__ import annotations

from typing import AsyncGenerator

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event, EventActions
from google.adk.apps.app import App
from opentelemetry import trace
from google.genai import types as genai_types

from kb_adk.otel import setup_tracing_if_enabled

from src.agents.agent_root import run_agent_root
from src.agents.subagent_document_processor import run_subagent_document_processor
from src.agents.subagent_domain_lifecycle import run_subagent_domain_lifecycle
from kb_adk.run_config import from_env as run_config_from_env


def _content_from_text(text: str) -> genai_types.Content:
    return genai_types.Content(role="model", parts=[genai_types.Part(text=text or "")])


def _apply_run_config(callback_context: CallbackContext):
    setup_tracing_if_enabled()
    span = trace.get_current_span()
    if callback_context and hasattr(callback_context, "invocation_context"):
        ctx = callback_context.invocation_context
        if ctx.run_config is None:
            ctx.run_config = run_config_from_env()
        if span:
            try:
                span.set_attribute("session.id", ctx.session.id)
                span.set_attribute("app.name", ctx.app_name)
            except Exception:
                pass
    elif callback_context and hasattr(callback_context, "run_config"):
        if callback_context.run_config is None:
            callback_context.run_config = run_config_from_env()
        if span:
            try:
                span.set_attribute("session.id", getattr(callback_context, "session_id", ""))
            except Exception:
                pass
    return None


class KbDocumentAgent(BaseAgent):
    name: str = "subagent_document_processor"
    description: str = "Processes documents/URLs, extracts facts, saves selections."

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        payload = {
            "session_id": ctx.session.id,
            "raw_text": ctx.user_content.parts[0].text if ctx.user_content and ctx.user_content.parts else "",
        }
        response = run_subagent_document_processor(payload, session_id=ctx.session.id, session_state=dict(ctx.session.state))
        state_delta = response.pop("state_delta", {}) or {}
        text = response.get("message_to_user") or response.get("response_message") or response.get("reasoning") or ""
        actions = EventActions(state_delta=state_delta, end_of_agent=True)
        yield Event(invocation_id=ctx.invocation_id, author=self.name, branch=ctx.branch, content=_content_from_text(text), actions=actions)


class KbDomainAgent(BaseAgent):
    name: str = "subagent_domain_lifecycle"
    description: str = "Handles domain create/update flows."

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        payload = {
            "session_id": ctx.session.id,
            "operation_type": ctx.session.state.get("intent"),
            "user_input": ctx.user_content.parts[0].text if ctx.user_content and ctx.user_content.parts else "",
            "confirmation_status": ctx.session.state.get("confirmation_status", False),
        }
        response = run_subagent_domain_lifecycle(payload, session_id=ctx.session.id, session_state=dict(ctx.session.state))
        state_delta = response.pop("state_delta", {}) or {}
        text = response.get("message_to_user") or response.get("response_message") or response.get("reasoning") or ""
        actions = EventActions(state_delta=state_delta, end_of_agent=True)
        yield Event(invocation_id=ctx.invocation_id, author=self.name, branch=ctx.branch, content=_content_from_text(text), actions=actions)


class KbRootAgent(BaseAgent):
    name: str = "kb_root"
    description: str = "Knowledge base domains root agent (legacy flow wrapped for ADK)."

    def __init__(self):
        super().__init__(
            name="kb_root",
            description="Knowledge base domains root agent (legacy flow wrapped for ADK).",
            sub_agents=[KbDomainAgent(), KbDocumentAgent()],
            before_agent_callback=_apply_run_config,
        )

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        user_message = ""
        if ctx.user_content and ctx.user_content.parts:
            user_message = "".join(part.text or "" for part in ctx.user_content.parts if hasattr(part, "text"))

        session_state = dict(ctx.session.state or {})
        response = run_agent_root(user_message, session_state=session_state, session_id=ctx.session.id)

        state_delta = response.pop("state_delta", {}) or {}

        if response.get("status") == "DELEGATE":
            target = response.get("delegation_target")
            actions = EventActions(state_delta=state_delta, transfer_to_agent=target)
            yield Event(invocation_id=ctx.invocation_id, author=self.name, branch=ctx.branch, actions=actions)
            return

        text = response.get("response_message") or response.get("message_to_user") or response.get("reasoning") or ""
        actions = EventActions(state_delta=state_delta, end_of_agent=True)
        yield Event(invocation_id=ctx.invocation_id, author=self.name, branch=ctx.branch, content=_content_from_text(text), actions=actions)


root_agent = KbRootAgent()
