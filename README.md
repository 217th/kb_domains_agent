# KB Domains Agent

CLI- and API-driven multi-agent system (Google ADK style) with mock/real modes for Gemini and Firestore. Structured logging and tracing to GCP are opt-in.

---

## Problem Statement
The accelerating pace of information generation in the modern world presents a significant challenge for users attempting to stay current. Users are required to dedicate substantial time and effort to monitoring a constantly expanding volume of diverse sources, including articles, videos, research papers, and news updates, to ensure they do not miss any significant, valuable, or relevant information.

This necessity leads to a dilemma:
1.  **Time Sink:** Users spend a considerable amount of time simply reviewing and filtering sources to confirm nothing important has been overlooked, which detracts from their ability to execute other critical tasks.
2.  **Information Overload & Gap:** Alternatively, users choose to dedicate less time to monitoring, resulting in missed essential articles, new sources, and, consequently, a failure to keep abreast of crucial events, developments, and changes in their respective fields.

The core problem is the **inefficient and time-consuming manual process of comprehensive information monitoring** against a backdrop of rapid technological and informational growth.

## Solution Statement
The proposed solution is the development of **Personal knowledge base agent** designed to automate and personalize the information monitoring process.

1.  **Personalized Topic Mapping:** The agent will maintain a detailed understanding of the user's specific subject matter interests, domain knowledge, and preferred topics to ensure accurate identification of content the user cannot afford to miss.
2.  **Source Processing and Relevance Filtering:** The agent will be capable of processing diverse content types, including web links, YouTube videos, and PDF documents. It will evaluate the relevance of each source against the user's defined interests.
3.  **Fact Extraction and Synthesis:** If a source is deemed relevant, the agent will automatically extract and synthesize key facts and data points that directly pertain to the user's specified topics.
4.  **Knowledge Base Integration:** The agent will provide the user with the option to save these relevant, extracted facts into a centralized, persistent Knowledge Base.

Subsequently, the user will be able to interact with the Knowledge Base by requesting:
* **Simplified Snapshots:** Concise overviews of the knowledge base content pertaining to a specific topic.
* **Detailed Reports:** Comprehensive listings of all relevant facts, including their full text and source attribution.

This system effectively addresses the information overload problem by transforming passive monitoring into an **active, personalized, and efficient knowledge acquisition process**.

## Architecture

Key concepts used in this project:
- Agent powered by an LLM
- Custom tools
- Long-term memory
- Observability: Logging, Tracing

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F30478268%2Fabfd7f02b76029447c140418bfc2e3b0%2Fcomponent_architecture.jpg?generation=1764596953453729&alt=media)

### `agent_root`
The Knowledge System Orchestrator is the entry point, managing user sessions and authentication. Its logic routes requests (e.g., content ingestion, domain management, snapshot generation) to specialized sub-agents or storage tools. Its main interfaces are the user message and internal sub-agents/tools.

### `subagent_domain_lifecycle`
The Domain Lifecycle Manager is a specialized agent responsible for the creation and modification of user-defined knowledge domains. Its main goal is to ensure data integrity by using the `tool_prettify_domain_description` to structure raw user input into standardized **Name, Description, and Keywords**. The logic enforces explicit user confirmation of the structured draft before persisting the domain data to Firestore via the `firestore_connector`.

### `subagent_document_processor`
The Knowledge Acquisition Specialist processes content from URLs (Web, PDF, YouTube), retrieving facts relevant to the user's active knowledge domains. It uses specialized tools to fetch, classify, and extract facts, requiring a user review step before securely archiving confirmed knowledge in the Memory Bank.

### `tool_auth_user`
This component, the User Identity Resolver, authenticates a user by checking the provided **username** against the Google Firestore database. Its internal logic either retrieves an existing `user_id` or creates a new user record and ID, returning the ID and a flag indicating if the user is new.

### `tool_toggle_domain_status`
This component, the Domain State Toggler, manages the **Active/Inactive status** of a specific user knowledge domain in Google Firestore. It validates the user and domain, inverts the current status, persists the change to the database, and returns the previous and new states for confirmation.

### `tool_fetch_user_knowledge_domains`
This component, the Knowledge Domain Fetcher, retrieves a user's list of knowledge domains (interests) from Google Firestore. Its logic validates the user ID, filters the list by Active or Inactive status if requested, and formats the output based on the specified `view_mode` (Brief or Detailed, which includes descriptions and keywords).

### `tool_generate_domain_snapshot`
This component, the Domain Content Snapshot Generator, creates a summarized overview of a user's knowledge domain. Its logic involves fetching all recorded facts from the Facts Storage, calculating metadata (e.g., fact count), and leveraging an external LLM to synthesize these facts into two outputs: a concise 'Super Summary' and a longer 'Extended Summary'.

### `tool_export_detailed_domain_snapshot`
This component, the Domain Detail Exporter, generates a comprehensive Markdown report of all metadata and associated facts for a specified user domain. Its logic fetches data from Firestore Facts Storage, compiles the content, and then securely uploads the final report to S3 storage, returning the user a download URL and file size.

### `tool_prettify_domain_description`
This component, the Domain Definition Prettifier, uses an external LLM to analyze raw user text describing a topic. Its logic decomposes the input into a structured, formalized Domain definition containing a concise Name, a comprehensive Description, and a list of relevant Keywords, returning this object for user review.

### `tool_process_ordinary_page`, `tool_process_pdf_link`, `tool_process_youtube_link`
These three content processing components specialize in data ingestion from external sources (YouTube, PDF, and general Web pages). They implement logic to **extract the main readable text** (transcript, embedded text, or cleaned article) from the specific URL type, providing the raw content for subsequent fact mining, while handling various source-specific errors.

### `tool_define_topic_relevance`
This component, the Domain Relevance Scorer, assesses how closely text content aligns with a specific user Knowledge Domain. Its logic constructs a prompt using the domain's metadata (description/keywords) and the target text, sending this to LLM to generate a normalized semantic relevance score (0.0 to 1.0).

### `tool_extract_facts_from_text`
This component, the Atomic Fact Miner, uses an LLM to analyze provided text content against a specific user Knowledge Domain (using its description and keywords). The core logic is to identify and extract distinct, verifiable factual statements, assign a unique, human-readable ID (slug) to each one, and return a structured list of these atomic facts for storage.

### `tool_save_fact_to_memory`
This component, the Memory Bank Fact Saver, is responsible for archiving verified knowledge. It receives a single fact text and required metadata (User ID, Domain ID, URL) and uses the operation to securely persist the data into the Facts Storage in Firestora, returning the new record's ID.

## Conclusion
Implementing the Personal KB Agent delivers two primary categories of benefits: efficiency and knowledge quality.

**Efficiency Gains:**
The agent significantly reduces the time required for primary document analysis, potentially saving expert users up to an hour per day currently spent on manual filtering. Content is delivered in a highly compressed and actionable format, ensuring quick consumption of critical data.

**Knowledge Enhancement:**
By automating comprehensive monitoring, the solution ensures users do not miss crucial events, critical news, or significant industry developments. Furthermore, the Knowledge Base provides users with reusable, synthesized knowledge extracts. This repository can be readily compiled, applied, and leveraged for secondary tasks, such as generating reports, informing decision-making, or accelerating the creation of new articles and content. Full traceability is maintained, as the agent always preserves the original source link for accessing complete context when required.

---

## Quickstart
- Python 3.13, `pip install -r requirements.txt`
- Create `.venv`: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Copy `.env.example` → `.env` and fill creds/flags.
- CLI chat: `./adk chat` (keeps pending domain drafts; reply `confirm` to save).
- API harness: `./adk web` (FastAPI on :8000, endpoints: `/agent-root`, `/subagent-domain-lifecycle`, `/subagent-document-processor`).

## Environment Configuration
Set in `.env` (see `.env.example`):
- `GOOGLE_APPLICATION_CREDENTIALS`: path to service account JSON (Firestore/Logging/Trace).
- `GOOGLE_CLOUD_PROJECT`: GCP project ID.
- `FIRESTORE_DATABASE`: e.g., `kb-agent` (prod) or `kb-agent-test1` (test).
- `GOOGLE_API_KEY`: required when `RUN_REAL_AI=1` (Gemini).
- `RUN_REAL_AI`: `1` → call Gemini; `0` → mock relevance/facts/prettify.
- `RUN_REAL_MEMORY`: `1` → save facts to Firestore (`MEMORY_COLLECTION_NAME`); `0` → mock IDs.
- `RUN_REAL_DOMAINS`: `1` → save domains to Firestore; `0` → mock save.
- `ENABLE_GCP_LOGGING`: `1` → send logs/traces to Cloud Logging/Trace; `0` → stdout only.
- `ENABLE_LOGGING_DEBUG`: `1` → print logging/trace send errors to stderr (helps diagnose missing traces).
- `MEMORY_COLLECTION_NAME`: Firestore collection for facts when `RUN_REAL_MEMORY=1`.

## Logging & Tracing (GCP)
- Enable APIs: `logging.googleapis.com`, `cloudtrace.googleapis.com`.
- Export `ENABLE_GCP_LOGGING=1` with creds/project before running chat/API.
- Logs: Cloud Logging, resource `global`, log name `structured`.
- Traces: Cloud Trace v2; use Trace Explorer. Set `ENABLE_LOGGING_DEBUG=1` to see send errors locally.
- Hand-off events are logged (`HANDOFF`, `DOC_CLASSIFIED`, `FACT_SAVE_BATCH`, etc.) and spans wrap agent/subagent turns.

## Running Modes
- Mock (default): `RUN_REAL_AI=0`, `RUN_REAL_MEMORY=0`, `RUN_REAL_DOMAINS=0`.
- Real AI: set `RUN_REAL_AI=1` (+ `GOOGLE_API_KEY`).
- Real memory: set `RUN_REAL_MEMORY=1` (uses Firestore `MEMORY_COLLECTION_NAME`).
- Real domains: set `RUN_REAL_DOMAINS=1` (domains collection in Firestore).
- GCP telemetry: set `ENABLE_GCP_LOGGING=1` (optional `ENABLE_LOGGING_DEBUG=1`).

## Running
- CLI chat: `./adk chat`
  - Domain lifecycle is multi-turn: first reply shows draft; type `confirm` to save (mock or Firestore if `RUN_REAL_DOMAINS=1`).
- API harness: `./adk web` → use the JSON endpoints; status, hand-off, and spans are logged.

## Tests
- Offline/unit/e2e: `.venv/bin/python -m pytest tests/unit tests/e2e`
- Firestore real: `FIRESTORE_DATABASE=kb-agent .venv/bin/python -m pytest tests/integration/test_firestore_real.py -vv`
- Memory real: `RUN_REAL_MEMORY=1 FIRESTORE_DATABASE=kb-agent .venv/bin/python -m pytest tests/integration/test_memory_real.py -vv`
- Content real (opt-in): `RUN_REAL_CONTENT_TESTS=1 .venv/bin/python -m pytest tests/integration/test_content_real.py`

## Notes
- Hand-off and span logs include masked args; secrets are filtered in logger.
- If Cloud Trace/Logging don’t show data, set `ENABLE_LOGGING_DEBUG=1` to surface send errors and verify network to GCP endpoints.
