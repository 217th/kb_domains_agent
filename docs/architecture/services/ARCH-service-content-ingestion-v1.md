---
id: ARCH-service-content-ingestion
title: "Service: Content Ingestion"
type: service
layer: infrastructure
owner: @team-ai
version: v1
status: current
created: 2025-12-02
updated: 2025-12-02
tags: [scraping, pdf, youtube]
depends_on: []
referenced_by: []
---
## Context
Responsible for fetching and extracting raw text from various external sources (Web, PDF, YouTube) to support knowledge acquisition.

## Structure
*   **File:** `src/tools/content.py`
*   **Key Functions:**
    *   `tool_process_ordinary_page`: Uses `requests` and `BeautifulSoup`.
    *   `tool_process_pdf_link`: Uses `pypdf`.
    *   `tool_process_youtube_link`: Uses `youtube_transcript_api`.

## Behavior
*   **Web:** Fetches HTML, cleans scripts/styles, extracts text.
*   **PDF:** Downloads stream, extracts text from pages.
*   **YouTube:** Extracts video ID, fetches transcript.
*   **Error Handling:** Maps HTTP errors and parsing failures to standardized error codes.

## Evolution
### Historical
*   v1: Support for HTML, PDF, and YouTube transcripts.
