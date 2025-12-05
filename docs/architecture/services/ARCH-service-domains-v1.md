---
id: ARCH-service-domains
title: "Service: Domains Management"
type: service
layer: domain
owner: @team-core
version: v1
status: current
created: 2025-12-02
updated: 2025-12-02
tags: [domains, firestore, snapshots]
depends_on: [ARCH-service-knowledge-processing]
referenced_by: []
---
## Context
Manages the lifecycle, retrieval, and reporting of User Knowledge Domains.

## Structure
*   **File:** `src/tools/domains.py`
*   **Key Functions:**
    *   `tool_fetch_user_knowledge_domains`: Retrieves domains from Firestore.
    *   `tool_toggle_domain_status`: Toggles active/inactive state.
    *   `tool_prettify_domain_description`: Delegates to AI analysis to structure domain input.
    *   `tool_generate_domain_snapshot`: Generates summaries (mocked).
    *   `tool_export_detailed_domain_snapshot`: Exports reports (mocked).

## Behavior
*   **Persistence:** Interacts with the `domains` collection in Firestore.
*   **Filtering:** Supports filtering by status (ACTIVE/INACTIVE) and view modes (BRIEF/DETAILED).
*   **AI Integration:** Uses `ARCH-service-knowledge-processing` (via `ai_analysis`) for domain prettification.

## Evolution
### Historical
*   v1: Firestore CRUD, status toggling, and mocked snapshot/export capabilities.
