---
id: TASK-2025-003
title: "Implement Content Ingestion & Knowledge Processing"
status: done
priority: high
type: feature
estimate: 24h
assignee: @team-ai
created: 2025-12-02
updated: 2025-12-02
parents: []
children: []
arch_refs: [ARCH-service-content-ingestion, ARCH-service-knowledge-processing, ARCH-service-memory, ARCH-subagent-document-processor]
audit_log:
  - {date: 2025-12-02, user: "@AI-DocArchitect", action: "created with status done"}
---
## Description
Build the pipeline for fetching content from URLs, analyzing relevance using Gemini, extracting facts, and saving them to memory.

## Acceptance Criteria
1.  Content tools support Web, PDF, and YouTube.
2.  `ai_analysis` tools interface with Gemini for scoring and extraction.
3.  `subagent_document_processor` orchestrates the fetch-analyze-save workflow.
4.  Facts are saved to Firestore via `tool_save_fact_to_memory`.

## Definition of Done
*   Code implemented in `src/tools/content.py`, `src/tools/ai_analysis.py`, `src/tools/memory.py`, `src/agents/subagent_document_processor.py`.
*   Integration tests passed (`tests/integration/test_content_real.py`, `tests/integration/test_memory_real.py`).
*   E2E tests passed (`tests/e2e/test_doc_processor.py`).

## Notes
Includes `RUN_REAL_AI` and `RUN_REAL_MEMORY` flags for cost control.
