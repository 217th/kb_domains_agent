---
id: ARCH-agent-root
title: "Agent Root (Orchestrator)"
type: agent
layer: application
owner: @team-core
version: v1
status: current
created: 2025-12-02
updated: 2025-12-02
tags: [orchestrator, routing, auth]
depends_on: [ARCH-service-auth, ARCH-service-domains, ARCH-subagent-domain-lifecycle, ARCH-subagent-document-processor]
referenced_by: []
---
## Context
The **Agent Root** acts as the central orchestrator and entry point for the Knowledge Base system. It manages user sessions, authenticates identities, and routes user intents to specialized sub-agents or tools. It ensures that unauthenticated users cannot access sensitive operations.

## Structure
*   **File:** `src/agents/agent_root.py`
*   **Key Functions:**
    *   `run_agent_root(user_message, session_user_id)`: Main entry point.
    *   `_classify_intent(message)`: Determines if the user wants to process a URL, manage domains, or perform other actions.
    *   `_detect_name(message)`: Heuristic for extracting names from introduction messages.

## Behavior
The agent operates in a multi-phase workflow:

1.  **Authentication & State Check:**
    *   Checks for `session_user_id`.
    *   If missing, attempts to authenticate via `ARCH-service-auth` using a name found in the message.
    *   On success, fetches and displays user domains via `ARCH-service-domains`.

2.  **Intent Classification & Routing:**
    *   **URL Detection:** Routes to `ARCH-subagent-document-processor`.
    *   **Domain Lifecycle:** Routes to `ARCH-subagent-domain-lifecycle` for creation/updates.
    *   **Toggle/Snapshot/Export:** Directly calls `ARCH-service-domains` tools.

3.  **Handoff:**
    *   Returns a `DELEGATE` status with a payload when handing off to sub-agents.
    *   Logs `HANDOFF` events for telemetry.

## Evolution
### Historical
*   v1: Initial implementation with regex-based routing and direct tool integration.
