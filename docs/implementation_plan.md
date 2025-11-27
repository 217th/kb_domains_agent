# IMPLEMENTATION PLAN: Google ADK Multi-Agent System (v4.0)

**Strategy:** "Walking Skeleton" (Layered Implementation).
**Tech Stack:** Python 3.13, Google ADK, Firestore, Vertex AI.

-----

## PHASE 0: Environment & Cloud Setup (BOOTSTRAP)

**Goal:** Prepare the local environment, configure Google Cloud Platform (GCP), and set up access rights. **Blocking Phase:** Agent code cannot run without this step.

### Steps

#### Step 0.1: Google Cloud Project Provisioning

1.  **Project Creation:** Create a new Google Cloud Project (or select an existing one).
2.  **API Enablement:** Enable the following mandatory APIs:
      * `aiplatform.googleapis.com` (Vertex AI / Gemini)
      * `firestore.googleapis.com` (Native Mode Database)
      * `cloudtrace.googleapis.com` (Trace)
      * `logging.googleapis.com` (Logging)
      * `secretmanager.googleapis.com` (Optional, for better secret management)
3.  **Service Account (SA):** Create a service account `agent-backend-sa`.
      * **Roles:**
          * `roles/datastore.user` (Firestore Read/Write)
          * `roles/aiplatform.user` (Gemini/Vertex Invocation)
          * `roles/logging.logWriter` (Log writing)
          * `roles/cloudtrace.agent` (Trace submission)
      * **Key:** Generate a JSON key and save it locally (add path to `.env`).

#### Step 0.2: Cloud Infrastructure Init

1.  **Firestore:** Initialize the database in **Native Mode**.
      * Create empty collections: `users`, `knowledge_domains`.
2.  **Vertex AI Agent Engine:**
      * Activate Agent Engine in the console.
      * Ensure the region supports Gemini Pro 1.5.

#### Step 0.3: Local Dev Environment

1.  **Python Setup:** Install Python 3.13. Create a virtual environment (`venv`).
2.  **Dependencies Installation:** Create and install `requirements.txt`:
    ```text
    # Core Google Cloud
    google-cloud-aiplatform>=1.38.0  # Vertex AI & GenAI
    google-cloud-firestore>=2.14.0   # Database
    google-cloud-logging>=3.9.0      # Observability
    google-cloud-trace>=1.11.0       # Observability

    # Agent Framework & Utilities
    pydantic>=2.5.0                  # Data Validation
    python-dotenv>=1.0.0             # Secrets Management
    PyYAML>=6.0                      # Config Parsing
    tenacity>=8.2.0                  # Retries

    # Tool Specifics
    youtube-transcript-api>=0.6.1    # tool_process_youtube_link
    beautifulsoup4>=4.12.0           # tool_process_ordinary_page
    httpx>=0.26.0                    # tool_process_pdf_link (Streaming)
    boto3>=1.34.0                    # tool_export_detailed_domain_snapshot (S3)
    markdown>=3.5.0                  # Formatting reports
    ```
3.  **Config Initialization:**
      * Create `.env` based on a template.
      * Add variables: `GOOGLE_APPLICATION_CREDENTIALS` (path to JSON key), `GOOGLE_CLOUD_PROJECT`, `GOOGLE_API_KEY` (if using AI Studio, though Vertex AI SA is preferred).

### Verification (Definition of Done)

  * **Check 1:** Command `gcloud projects describe <PROJECT_ID>` returns active status.
  * **Check 2:** Script `python -c "import google.cloud.firestore; print('Success')"` executes without errors.
  * **Check 3:** Firestore collections are visible in the GCP console.

-----

## PHASE 1: Foundation & Configuration Infrastructure

**Goal:** Initialize the application skeleton, enforce configuration decoupling, and set up observability primitives.

### Steps

1.  **Config Decoupling:**
      * Create `config.yaml`: Store model parameters (temp, top-k), `relevance_threshold` (default 0.7).
      * Create `prompts.yaml`: Extract all `system_instruction` texts from the JSON specifications into this file.
2.  **Observability Module:**
      * Implement `logger.py`.
      * **Feature:** `mask_pii(text)` function to truncate texts \> 200 chars.
      * **Feature:** JSON logging with fields: `trace_id`, `prompt_version_hash`, `model_config_id`.

### Verification (Definition of Done)

  * **Test T-15 (Secrets):** Run app without `.env`. Assert system crash/exit.
  * **Test T-13 (Tracing):** Verify logs contain `prompt_version_hash`.

-----

## PHASE 2: Routing Core & Authentication

**Goal:** Implement `agent_root` and User Authentication.

### Steps

1.  **Tool Implementation:**
      * Implement `tool_auth_user.py` connected to **Firestore** (Collection: `users`).
2.  **Agent Implementation:**
      * Implement `agent_root.py`.
      * Load prompts from `prompts.yaml`.
      * Implement **Route Classification**:
          * URL regex detection -\> Route to `subagent_document_processor`.
          * Keywords ("create", "edit") -\> Route to `subagent_domain_lifecycle`.
          * Keywords ("export") -\> Route to `tool_export_detailed_domain_snapshot`.
3.  **Mocking:**
      * Create "Mock" versions of `subagent_document_processor` and `subagent_domain_lifecycle` that simply return a success message.

### Verification (Definition of Done)

  * **Test T-01 (Routing):** Input URL -\> Verify delegation to Doc Processor. Input "Create topic" -\> Delegation to Lifecycle.
  * **Test T-02 (Auth):** Input "Hello" (no ID) -\> Verify agent calls `tool_auth_user`.
  * **Test T-08 (Errors):** Simulate Firestore downtime. Verify user gets a friendly error message.

-----

## PHASE 3: Domain Lifecycle (Ontology)

**Goal:** Enable users to Create, Update, and Toggle Knowledge Domains in Firestore.

### Steps

1.  **Tools Implementation:**
      * `tool_fetch_user_knowledge_domains` (Firestore Read).
      * `tool_toggle_domain_status` (Firestore Update).
      * `tool_prettify_domain_description` (LLM Call - Gemini).
2.  **Agent Implementation:**
      * Implement `subagent_domain_lifecycle.py`.
      * Logic: Receive raw text -\> Call Prettify -\> **Wait for Confirmation** -\> Write to Firestore.

### Verification (Definition of Done)

  * **Test T-03 (Confirmation Loop):** Send `confirmation_status=false`. Assert NO write to Firestore.
  * **Test T-09 (Structure):** Verify "raw text" is converted to structured JSON (Name, Keywords).

-----

## PHASE 4: Content Discovery (Analysis Only)

**Goal:** Fetch content from URLs, determine relevance, and extract candidate facts. **(No saving yet)**.

### Steps

1.  **Fetch Tools:**
      * `tool_process_pdf_link` (Stream/Parse via `httpx`).
      * `tool_process_youtube_link` (Transcript API via `youtube-transcript-api`).
      * `tool_process_ordinary_page` (Scraper via `bs4`).
2.  **Intelligence Tools:**
      * `tool_define_topic_relevance`: Compare content vs. Domain using `relevance_threshold`.
      * `tool_extract_facts_from_text`: Extract atomic facts with IDs.
3.  **Agent Logic (Phases 1-3):**
      * Implement `subagent_document_processor`.
      * **Logic:** Detect URL Type -\> Fetch Content -\> Fetch Active Domains -\> Check Relevance -\> Extract Facts.
      * **Output:** Return `status: "review_required"` with `candidate_facts` array.

### Verification (Definition of Done)

  * **Test T-04 (URL Heuristics):** Verify correct tool selection for PDF vs. YouTube.
  * **Test T-10 (Threshold):** Feed irrelevant text. Verify `relevance_score` \< 0.7 triggers discard.
  * **Test T-05 (Contract):** Verify output JSON includes `source_url` in `candidate_facts`.

-----

## PHASE 5: Knowledge Persistence (Memory Bank)

**Goal:** Implement the "Write" side of the Memory Bank using Vertex AI.

### Steps

1.  **Tool Implementation:**
      * Implement `tool_save_fact_to_memory.json`.
      * **Integration:** Connect to **Vertex AI Agent Engine** (CreateMemory API).
      * **Scope:** Must map `source_url` and `user_id` to the memory scope.
2.  **Agent Logic (Phase 4):**
      * Update `subagent_document_processor`.
      * **Loop:** Receive `selected_fact_ids` -\> Iterate `facts_payload` -\> Call `tool_save_fact_to_memory` for each match.
3.  **Observability:**
      * Ensure `tool_save_fact_to_memory` creates a **Child Span** of the parent `save_facts_batch` span.
      * Log masking: Truncate `fact_text` to 200 chars.

### Verification (Definition of Done)

  * **Test T-06 (Batch Loop):** Select 3 facts. Verify tool is called exactly 3 times.
  * **Test T-07 (Atomic Write):** Verify `memory_id` is returned on success.
  * **Test T-16 (Metrics):** Check `mas/fact_save_latency` metric generation.

-----

## PHASE 6: Reporting & Exports

**Goal:** Enable reading from Memory Bank and generating reports.

### Steps

1.  **Tools Implementation:**
      * `tool_generate_domain_snapshot`: Read from Memory Bank -\> LLM Summary.
      * `tool_export_detailed_domain_snapshot`: Aggregate Data -\> Generate Markdown -\> Upload to S3 -\> Return Link.
2.  **Integration:**
      * Ensure `agent_root` correctly routes "summary" and "export" requests to these tools.

### Verification (Definition of Done)

  * **Manual Verification:** Request "Export detailed report". Verify the returned URL downloads a valid Markdown file containing facts saved in Phase 5.

-----

### IMPLEMENTATION MATRIX (v4.0)

| Category | Component / Artifact | **Phase 0: Env Setup** | **Phase 1: Infra** | **Phase 2: Core** | **Phase 3: Ontology** | **Phase 4: Content** | **Phase 5: Memory** | **Phase 6: Reporting** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CLOUD** | **GCP Project & IAM** | ✅ **Real** (SAs, APIs) | — | — | — | — | — | — |
| | **DB: Firestore** | ✅ **Real** (Init) | — | — | — | — | — | — |
| | **DB: Vertex Agent** | ✅ **Real** (Enable) | — | — | — | — | ✅ **Real** (Write) | 🔄 **Update** (Read) |
| **INFRA** | **Dependencies** | ✅ **Real** (`pip`) | — | — | — | — | — | — |
| | **Secrets (.env)** | ⚙️ Template | ✅ **Real** (Load) | — | — | — | — | — |
| | **Logging / Trace** | — | ✅ **Real** (Lib) | ✅ **Real** (Trace) | — | — | 🔄 **Update** (Child) | — |
| **AGENTS** | `agent_root` | — | ⚙️ Prompts | ✅ **Real** (Logic) | 🔄 **Update** (Fetch) | — | — | 🔄 **Update** (Report) |
| | `subagent_lifecycle` | — | ⚙️ Prompts | 🎭 **Mock** | ✅ **Real** (CRUD) | — | — | — |
| | `subagent_doc_proc` | — | ⚙️ Prompts | 🎭 **Mock** | — | ✅ **Real** (Analysis) | 🔄 **Update** (Save) | — |
| **TOOLS** | `tool_auth_user` | — | — | ✅ **Real** (Firestore) | — | — | — | — |
| | `tool_fetch_domains` | — | — | 🎭 **Mock** | ✅ **Real** (Read) | — | — | — |
| | `tool_toggle_status` | — | — | — | ✅ **Real** (Update) | — | — | — |
| | `tool_prettify` | — | — | — | ✅ **Real** (LLM) | — | — | — |
| | `tool_process_*` | — | — | — | — | ✅ **Real** (Fetch) | — | — |
| | `tool_define_relev` | — | — | — | — | ✅ **Real** (LLM) | — | — |
| | `tool_save_memory` | — | — | — | — | 🎭 **Mock** | ✅ **Real** (Vertex) | — |
| | `tool_export/snap` | — | — | — | — | — | — | ✅ **Real** (S3/LLM) |

**Legend:**

  * ⚪ **Pending:** Not started / Out of scope.
  * ⚙️ **Config:** Configuration, setup, or interface definition only.
  * 🎭 **Mock:** Hardcoded "Happy Path" response (Stub).
  * ✅ **Real:** Fully implemented business logic.
  * 🔄 **Update:** Refactoring or extending existing component.