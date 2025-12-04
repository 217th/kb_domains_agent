---
id: ARCH-subagent-domain-lifecycle
title: "Subagent: Domain Lifecycle"
type: agent
layer: application
owner: @team-core
version: v1
status: current
created: 2025-12-02
updated: 2025-12-02
tags: [domains, crud, ai-assistance]
depends_on: [ARCH-service-domains]
referenced_by: []
---
## Context
The **Domain Lifecycle** sub-agent manages the creation and modification of user knowledge domains. It ensures that domains have high-quality descriptions and keywords by leveraging AI "prettification" before persistence.

## Structure
*   **File:** `src/agents/subagent_domain_lifecycle.py`
*   **Key Functions:**
    *   `run_subagent_domain_lifecycle(payload)`: Manages the drafting and confirmation loop.

## Behavior
1.  **Drafting:**
    *   Takes raw user input (e.g., "I like AI").
    *   Calls `tool_prettify_domain_description` (from `ARCH-service-domains`) to generate a structured draft (Name, Description, Keywords).
    *   Returns the draft to the user with status `AWAITING_USER_REVIEW`.

2.  **Confirmation & Persistence:**
    *   Receives `confirmation_status: True`.
    *   Persists the domain to Firestore (if `RUN_REAL_DOMAINS=1`) or mocks the save.
    *   Generates a unique Domain ID.

## Evolution
### Historical
*   v1: Implemented draft-confirm loop with Firestore integration.
