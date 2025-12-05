---
id: ARCH-service-knowledge-processing
title: "Service: AI Knowledge Processing"
type: service
layer: domain
owner: @team-ai
version: v1
status: current
created: 2025-12-02
updated: 2025-12-02
tags: [ai, gemini, relevance, extraction]
depends_on: [ARCH-infra-config]
referenced_by: []
---
## Context
Encapsulates AI logic for analyzing content relevance and extracting atomic facts using Google Gemini models.

## Structure
*   **File:** `src/tools/ai_analysis.py`
*   **Key Functions:**
    *   `tool_define_topic_relevance`: Scores content against domain metadata.
    *   `tool_extract_facts_from_text`: Extracts structured facts from relevant content.
    *   `tool_prettify_domain_description`: Structures raw domain descriptions.

## Behavior
*   **Model Integration:** Uses `google.generativeai` to call Gemini models.
*   **Configuration:** Loads model parameters and prompts via `ARCH-infra-config`.
*   **Mocking:** Supports `RUN_REAL_AI=0` for cost-free testing/development.
*   **Robustness:** Includes JSON parsing fallback for LLM outputs.

## Evolution
### Historical
*   v1: Gemini integration for relevance scoring, fact extraction, and domain prettification.
