---
id: ARCH-subagent-document-processor
title: "Subagent: Document Processor"
type: agent
layer: application
owner: @team-ai
version: v1
status: current
created: 2025-12-02
updated: 2025-12-02
tags: [ai, ingestion, facts]
depends_on: [ARCH-service-content-ingestion, ARCH-service-knowledge-processing, ARCH-service-memory, ARCH-service-domains]
referenced_by: []
---
## Context
The **Document Processor** is a specialized sub-agent responsible for ingesting content from URLs, analyzing it against the user's active domains, extracting relevant facts, and persisting them to memory.

## Structure
*   **File:** `src/agents/subagent_document_processor.py`
*   **Key Functions:**
    *   `run_subagent_document_processor(payload)`: Handles both discovery (extraction) and save phases.
    *   `_classify_url(url)`: Determines if content is PDF, YouTube, or Web.

## Behavior
The sub-agent operates in two distinct modes:

1.  **Discovery Mode:**
    *   Receives a URL.
    *   Fetches content via `ARCH-service-content-ingestion`.
    *   Retrieves active domains via `ARCH-service-domains`.
    *   For each domain, checks relevance and extracts facts using `ARCH-service-knowledge-processing`.
    *   Returns a list of `candidate_facts` with status `review_required`.

2.  **Save Mode:**
    *   Receives `selected_fact_ids` and `facts_payload`.
    *   Persists selected facts to `ARCH-service-memory`.

## Evolution
### Historical
*   v1: Implemented dual-mode workflow (Discovery/Save) with support for PDF, YouTube, and Web content.
