## Context
This repository implements a multi-agent knowledge management workflow (Google ADK style) for domain lifecycle and document ingestion. It orchestrates authentication, routing, and sub-agent delegation while supporting mock and real integrations with Gemini, Firestore, and memory persistence.

## Structure
- `src/agents/`: agent_root (auth/routing), subagent_domain_lifecycle (draft/confirm/save domains), subagent_document_processor (fetch content, relevance, fact extraction, save facts).
- `src/tools/`: Firestore-backed auth/domains/memory, content fetchers (web/PDF/YouTube), AI analysis (Gemini relevance/facts/prettify), with mock/real switches.
- `src/utils/`: config loader (env + YAML), structured logger, telemetry (spans/logs).
- `src/cli/chat.py`: interactive REPL; handles multi-turn domain confirmation.
- `server/adk_web.py`: FastAPI harness exposing agent endpoints.
- `config/`: prompts.yaml, config.yaml (model params, thresholds), observability config.
- `tests/`: unit, e2e, integration (Firehose/memory/content opt-in).

## Behavior
- agent_root: authenticates (Firestore), classifies intent (URL → doc processor; create/update domain → domain subagent; toggle/snapshots/export → tools), emits HANDOFF logs, returns delegation payloads.
- subagent_domain_lifecycle: prettifies domain text (Gemini or mock), returns draft, on confirm saves (mock or Firestore when `RUN_REAL_DOMAINS=1`).
- subagent_document_processor: classifies URL, fetches content, fetches active domains, computes relevance (Gemini or mock), extracts facts, returns candidate facts; save-mode commits selected facts (mock or Firestore when `RUN_REAL_MEMORY=1`). Logs key steps (`DOC_CLASSIFIED`, `FACT_SAVE_BATCH`, `FACT_EXTRACTION_FAILED`, etc.).
- Logging/Tracing: stdout JSON by default; Cloud Logging/Trace when `ENABLE_GCP_LOGGING=1` (debug via `ENABLE_LOGGING_DEBUG=1`). Spans wrap agent/subagent turns; hand-offs are logged.
- Feature flags: `RUN_REAL_AI` (Gemini), `RUN_REAL_MEMORY` (Firestore facts), `RUN_REAL_DOMAINS` (Firestore domains).

## Historical evolution
- v1: Initial mock agent flow and tool interfaces.
- v2: Real Firestore auth/domains; real content fetch; Gemini integration with safe fallbacks.
- v3: Memory persistence (Firestore), CLI multi-turn confirm, Cloud Logging/Trace toggles, hand-off tracing/logging.
