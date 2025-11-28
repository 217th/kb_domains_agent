# Phase 2: Detailed Implementation Roadmap (Revised)

**Selected Strategy:** Concept 1: The "Nervous System" (Skeleton First).
**Philosophy:** We will build the complete Agent Orchestration Graph immediately using **Mock Tools**. This allows us to validate the complex routing, state management, and `prompts.yaml` structure before dealing with database connections or external API flakes.

**Revision Note:** Added **Phase 0** for explicit environment and cloud infrastructure preparation.

---

### Step 2.1: The "Walking Skeleton" Implementation Matrix

| Component | Phase 0: Env & Infra | Phase 1: Foundation | Phase 2: The Mocked Brain | Phase 3: Real Tools |
| :--- | :--- | :--- | :--- | :--- |
| **Infra & Auth** | ✅ Real (GCP/Venv) | — | — | — |
| **Config & Logs** | — | ✅ Real (YAML/Env) | ✅ Real (Tracing) | — |
| **Agent: Root** | — | — | ✅ Real Logic / 🎭 Mocks | ✅ Real Logic / ✅ Real Tools |
| **Sub-Agents** | — | — | ✅ Real Logic / 🎭 Mocks | ✅ Real Logic / ✅ Real Tools |
| **Tools (All)** | — | — | 🎭 Mock (Static JSON) | ✅ Real (Firestore/Vertex) |

---

### Step 2.2: Step-by-Step Plan

#### PHASE 0: ENVIRONMENT & CLOUD PREPARATION

### [Step 0.1] Local Development Environment Setup
**Goal:** Prepare the Python environment and define the strict dependency list. **Effort:** Small.

*   **Justification:** Ensures reproducible builds and prevents "it works on my machine" issues.
*   **Scope & Dependencies:**
    *   Verify Python 3.13 installation.
    *   Create and activate a virtual environment (`.venv`).
    *   Create `requirements.txt` with pinned versions.
*   **Dependency List (Add to requirements.txt):**
    *   **Core/Utils:** `pydantic>=2.0`, `pydantic-settings`, `pyyaml`, `python-dotenv`.
    *   **Google Cloud:** `google-cloud-firestore`, `google-cloud-aiplatform` (Vertex AI), `google-generativeai` (Gemini), `google-cloud-logging`, `google-cloud-trace`.
    *   **Content Processing:** `requests`, `beautifulsoup4`, `pypdf`, `youtube-transcript-api`.
    *   **Testing/Dev:** `pytest`, `pytest-mock`.
*   **Definition of Done:**
    *   Command: `pip install -r requirements.txt && python -c "import google.cloud.firestore; import pydantic; print('Env Ready')"`
    *   Success Criteria: Prints "Env Ready" without import errors.

### [Step 0.2] Google Cloud Infrastructure Provisioning
**Goal:** Create the GCP Project, enable required APIs, and generate Service Account credentials. **Effort:** Medium.

*   **Justification:** The code in Phase 3 will fail immediately without these permissions.
*   **Scope & Dependencies:**
    *   **Project:** Create a new GCP Project (e.g., `agent-memory-bank-dev`).
    *   **APIs to Enable:**
        *   `firestore.googleapis.com` (Database)
        *   `aiplatform.googleapis.com` (Vertex AI)
        *   `generativelanguage.googleapis.com` (Gemini API)
        *   `logging.googleapis.com` (Cloud Logging)
        *   `cloudtrace.googleapis.com` (Cloud Trace)
    *   **IAM:** Create a Service Account (SA) named `agent-backend-sa`.
    *   **Roles:** Grant `Firestore User`, `Vertex AI User`, `Logs Writer`, `Cloud Trace Agent`.
    *   **Keys:** Download the JSON key file for this SA (save locally as `service_account.json` - **ADD TO .GITIGNORE**).
*   **Definition of Done:**
    *   Command: Manual Verification via GCP Console.
    *   Success Criteria: APIs are enabled, and you possess the `service_account.json` file.

### [Step 0.3] Secrets & Environment Configuration
**Goal:** Establish the secure configuration entry point. **Effort:** Small.

*   **Justification:** The application must never contain hardcoded keys.
*   **Scope & Dependencies:**
    *   Create `.env` file (add to `.gitignore`).
    *   Create `.env.example` (safe template).
*   **Required Variables:**
    ```ini
    GOOGLE_APPLICATION_CREDENTIALS="path/to/service_account.json"
    GOOGLE_CLOUD_PROJECT="your-project-id"
    # Optional: If using AI Studio API Key instead of Vertex SA
    GOOGLE_API_KEY="your-gemini-api-key"
    ```
*   **Definition of Done:**
    *   Command: `cat .env`
    *   Success Criteria: File exists and contains the paths/IDs from Step 0.2.

---

#### PHASE 1: FOUNDATION & CONFIGURATION

### [Step 1] Configuration Engine & Prompts Loader
**Goal:** Implement the strict separation of Code, Config, and Prompts. **Effort:** Small.

*   **Justification:** The `prompts.yaml` and `.env` requirements are strict constraints. Retrofitting them later is painful.
*   **Scope & Dependencies:**
    *   Create `config/prompts.yaml` (copy content from Agent JSONs "system_instruction").
    *   Create `config/config.yaml` (model parameters, thresholds).
    *   Implement `src/utils/config_loader.py` (Singleton pattern).
*   **Coding Instructions:**
    *   Use `pydantic-settings` or `pyyaml` for safe loading.
    *   Ensure `load_prompts()` returns a dictionary accessible by Agent ID.
    *   **Security:** Ensure the loader raises an error if credentials are missing in `.env`.
*   **Definition of Done:**
    *   Command: `python tests/unit/test_config.py`
    *   Criteria: Script prints a specific prompt string loaded from YAML and a config value (e.g., `temperature: 0.0`).

### [Step 2] Observability & Logging Wrapper
**Goal:** Implement standardized logging and tracing decorators to satisfy `observability.md`. **Effort:** Small.

*   **Justification:** We need to trace the execution flow across agents from Day 1 to debug the "Nervous System".
*   **Scope & Dependencies:**
    *   Implement `src/utils/logger.py` (Structured JSON logging).
    *   Implement `src/utils/telemetry.py` (Mockable tracing decorator).
*   **Coding Instructions:**
    *   Logger must support `mask_pii(text)` function (truncate >200 chars).
    *   Decorator `@trace_span` should capture `function_name` and `args` (masked).
    *   Ensure logs include `prompt_version_sha` (dummy value for now) as per requirements.
*   **Definition of Done:**
    *   Command: `python tests/unit/test_telemetry.py`
    *   Criteria: Output shows a JSON log entry with `severity: INFO` and a masked "fact_text" field.

---

#### PHASE 2: THE MOCKED NERVOUS SYSTEM

### [Step 3] Tool Interfaces & Mock Implementations
**Goal:** Define the Python functions for all 12 tools but implement them as **Mocks** returning static data. **Effort:** Medium.

*   **Justification:** Agents need valid callables to function. Mocks allow us to test Agent logic without paying for API calls.
*   **Scope & Dependencies:**
    *   Create `src/tools/auth.py`, `src/tools/domains.py`, `src/tools/content.py`, `src/tools/memory.py`.
    *   Implement all tools defined in the JSON specs.
*   **Mock Strategy:**
    *   **MOCKED:** All tools.
    *   Example: `tool_auth_user` returns `{"status": "success", "data": {"user_id": "mock_u1", "is_new_user": false}}`.
    *   Example: `tool_process_pdf_link` returns `{"content": "Mock PDF text about AI..."}`.
*   **Coding Instructions:**
    *   Use Pydantic models for Input/Output validation to enforce the JSON schemas strictly.
    *   Add artificial random delays (0.1s) to simulate network I/O.
*   **Definition of Done:**
    *   Command: `python tests/unit/test_tools_mock.py`
    *   Criteria: All 12 tools return valid JSON matching their spec schemas.

### [Step 4] Agent Root Implementation (Orchestrator)
**Goal:** Implement `agent_root` logic to handle Auth and Routing using the Mocks. **Effort:** Medium.

*   **Justification:** This is the entry point. We must verify it correctly identifies URLs vs. Domain Commands.
*   **Scope & Dependencies:**
    *   Implement `src/agents/agent_root.py`.
    *   Dependencies: `prompts.yaml` (Step 1), Mock Tools (Step 3).
*   **Mock Strategy:**
    *   **REAL:** Routing logic, Regex for URL detection, Prompt construction.
    *   **MOCKED:** `tool_auth_user`, `tool_fetch_user_knowledge_domains`.
*   **Coding Instructions:**
    *   Load system instruction from `prompts.yaml`.
    *   Implement the "PHASE 1" and "PHASE 2" logic from `agent_root.json`.
    *   **Crucial:** Return a structured object indicating `delegation_target` instead of actually calling the sub-agent class (dependency injection comes later).
*   **Definition of Done:**
    *   Command: `python tests/e2e/test_agent_root_flow.py`
    *   Criteria:
        *   Input "My name is Alice" -> Returns `SUCCESS` + Domain List (Mocked).
        *   Input "Check this http://example.com" -> Returns `DELEGATE` to `subagent_document_processor`.

### [Step 5] Sub-Agent: Domain Lifecycle (Mocked)
**Goal:** Implement the Create/Update domain workflow. **Effort:** Medium.

*   **Justification:** Verify the "Draft -> Confirm -> Save" loop without touching Firestore.
*   **Scope & Dependencies:**
    *   Implement `src/agents/subagent_domain_lifecycle.py`.
*   **Mock Strategy:**
    *   **REAL:** State machine (Drafting vs Saving).
    *   **MOCKED:** `tool_prettify_domain_description` (returns fixed keywords), `firestore_connector` (prints "Saved").
*   **Coding Instructions:**
    *   Logic: If `confirmation_status` is False, return draft. If True, call save tool.
    *   Ensure `tool_prettify` mock returns valid JSON structure (`name`, `description`, `keywords`).
*   **Definition of Done:**
    *   Command: `python tests/e2e/test_domain_lifecycle.py`
    *   Criteria: Two-turn conversation. Turn 1 returns "Review this draft". Turn 2 (Confirmed) returns "Saved".

### [Step 6] Sub-Agent: Document Processor (Mocked)
**Goal:** Implement the complex URL ingestion loop. **Effort:** Large.

*   **Justification:** This agent has the most complex logic (Relevance Loop -> Fact Extraction -> Batch Save). We must debug this flow with controllable mocks.
*   **Scope & Dependencies:**
    *   Implement `src/agents/subagent_document_processor.py`.
*   **Mock Strategy:**
    *   **REAL:** URL Classification (Regex), Relevance Filtering Logic, Batch Save Logic.
    *   **MOCKED:** `tool_process_*` (returns text), `tool_define_topic_relevance` (returns 0.9), `tool_extract_facts` (returns 2 facts).
*   **Coding Instructions:**
    *   Implement the "PHASE 3: RELEVANCE LOOP" strictly.
    *   **Critical Test:** Ensure `candidate_facts` output matches the input required for the "Save Mode" turn.
*   **Definition of Done:**
    *   Command: `python tests/e2e/test_doc_processor.py`
    *   Criteria:
        *   Input URL -> Returns `review_required` with 2 mock facts.
        *   Input `selected_fact_ids` -> Calls `tool_save_fact` 2 times (verified via Mock call count).

---

#### PHASE 3: WIRING THE HANDS (REAL TOOLS)

### [Step 7] Real Auth & Firestore Tools
**Goal:** Replace mocks with real Google Firestore implementations. **Effort:** Medium.

*   **Justification:** Persistent user/domain state is the backbone of the system.
*   **Scope & Dependencies:**
    *   Modify `src/tools/auth.py` and `src/tools/domains.py`.
    *   Requires `google-cloud-firestore` (Installed in Phase 0).
*   **Coding Instructions:**
    *   Use `GOOGLE_APPLICATION_CREDENTIALS` from env.
    *   Implement `tool_auth_user`: Check collection `users`.
    *   Implement `tool_fetch_...`: Query collection `domains` with filters.
*   **Definition of Done:**
    *   Command: `python tests/integration/test_firestore_real.py`
    *   Criteria: Run script twice. First time: "New User". Second time: "Existing User". Data visible in Firestore Console.

### [Step 8] Real Content Fetching Tools
**Goal:** Implement real web scraping and YouTube transcript fetching. **Effort:** Medium.

*   **Justification:** We need real text to test the LLM's extraction capabilities.
*   **Scope & Dependencies:**
    *   Modify `src/tools/content.py`.
    *   Libs: `requests`, `beautifulsoup4`, `youtube-transcript-api`.
*   **Coding Instructions:**
    *   **Security:** Use a User-Agent header for scraping.
    *   `tool_process_pdf_link`: Download to memory, use `pypdf` to extract text.
    *   `tool_process_youtube_link`: Handle `TranscriptsDisabled` exception gracefully.
*   **Definition of Done:**
    *   Command: `python tests/integration/test_content_real.py`
    *   Criteria: Successfully extracts text from a provided Wikipedia URL and a YouTube video ID.

### [Step 9] Real Intelligence Tools (Gemini)
**Goal:** Connect the AI tools to Google Gemini API. **Effort:** Medium.

*   **Justification:** Enable actual semantic analysis and fact extraction.
*   **Scope & Dependencies:**
    *   Modify `src/tools/ai_analysis.py` (Prettify, Relevance, Extract).
    *   Libs: `google-generativeai` or Vertex AI SDK.
*   **Coding Instructions:**
    *   Use `model_config` from `config.yaml`.
    *   Implement `tool_define_topic_relevance`: Send prompt, parse float score.
    *   Implement `tool_extract_facts_from_text`: Send prompt, parse JSON list.
*   **Definition of Done:**
    *   Command: `python tests/integration/test_ai_real.py`
    *   Criteria: Pass a text about "Apples" and domain "Fruit". Relevance score > 0.8. Facts extracted successfully.

### [Step 10] Real Memory Bank (Vertex AI)
**Goal:** Connect `tool_save_fact_to_memory` to Vertex AI Agent Engine. **Effort:** Medium.

*   **Justification:** Final step to complete the E2E loop.
*   **Scope & Dependencies:**
    *   Modify `src/tools/memory.py`.
*   **Coding Instructions:**
    *   Use `VertexAiMemoryBankService` (or equivalent REST API if SDK is limited).
    *   Map `domain_id` to the Memory Bank `topic`.
*   **Definition of Done:**
    *   Command: `python tests/integration/test_memory_real.py`
    *   Criteria: Successfully creates a memory record and returns a valid `memory_id` from Google Cloud.

---

### Execution Instructions for Codex CLI

1.  Start with **Phase 0 (Steps 0.1 - 0.3)**. Do not proceed until the environment is fully provisioned and validated.
2.  Proceed to **Phase 1** to lay the code foundation.
3.  In **Phase 2**, strictly implement Mocks. Do not try to connect to the Cloud services you set up in Phase 0 yet.
4.  In **Phase 3**, verify each Real Tool against the Cloud Infrastructure individually before running the full agent loop.