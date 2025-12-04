---
id: TASK-2025-002
title: "Implement Domain Management & Lifecycle"
status: done
priority: high
type: feature
estimate: 16h
assignee: @team-core
created: 2025-12-02
updated: 2025-12-02
parents: []
children: []
arch_refs: [ARCH-service-domains, ARCH-subagent-domain-lifecycle, ARCH-service-auth]
audit_log:
  - {date: 2025-12-02, user: "@AI-DocArchitect", action: "created with status done"}
---
## Description
Implement the tools and sub-agent required to manage user knowledge domains, including authentication, CRUD operations, and the AI-assisted creation workflow.

## Acceptance Criteria
1.  `tool_auth_user` authenticates or creates users in Firestore.
2.  `tool_fetch_user_knowledge_domains` retrieves domains with filtering.
3.  `subagent_domain_lifecycle` handles the draft-confirm loop using `tool_prettify_domain_description`.
4.  Domains are persisted to Firestore when confirmed.

## Definition of Done
*   Code implemented in `src/tools/domains.py`, `src/tools/auth.py`, `src/agents/subagent_domain_lifecycle.py`.
*   Integration tests passed (`tests/integration/test_firestore_real.py`).
*   E2E tests passed (`tests/e2e/test_domain_lifecycle.py`).

## Notes
Includes mock/real toggle via `RUN_REAL_DOMAINS`.
