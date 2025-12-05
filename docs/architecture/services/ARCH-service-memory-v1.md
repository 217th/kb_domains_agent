---
id: ARCH-service-memory
title: "Service: Memory (Fact Persistence)"
type: service
layer: infrastructure
owner: @team-data
version: v1
status: current
created: 2025-12-02
updated: 2025-12-02
tags: [memory, firestore, facts]
depends_on: []
referenced_by: []
---
## Context
Handles the secure persistence of confirmed facts into the long-term memory storage.

## Structure
*   **File:** `src/tools/memory.py`
*   **Key Function:** `tool_save_fact_to_memory(payload)`

## Behavior
*   **Persistence:** Saves facts to the configured Firestore collection (default: `memory_facts`).
*   **Data Model:** Stores `fact_text`, `source_url`, `user_id`, `domain_id`, and `created_at`.
*   **Mocking:** Supports `RUN_REAL_MEMORY=0` to return mock IDs without database writes.

## Evolution
### Historical
*   v1: Firestore-backed fact storage with mock capability.
