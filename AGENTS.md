# AGENTS.md

## `docs` directory
Contains project and system design artifacts of a multi-agent system using Google ADK.

- sequence_diagram.md - If I were you, I'd start with the sequence diagram. Then I'd delve into the specifications of each component.

- implementation_plan.md - CRITICAL: Follow this plan strictly. Complete development strictly according to phases and steps. Perform testing and explain the results to me at the end of each step. Explain to me how I can ensure that the step has been fully implemented.

1.  Start with **Phase 0 (Steps 0.1 - 0.3)**. Do not proceed until the environment is fully provisioned and validated.
2.  Proceed to **Phase 1** to lay the code foundation.
3.  In **Phase 2**, strictly implement Mocks. Do not try to connect to the Cloud services you set up in Phase 0 yet.
4.  In **Phase 3**, verify each Real Tool against the Cloud Infrastructure individually before running the full agent loop.

Agents specifications:
- agent_root.json
- subagent_document_processor.json
- subagent_domain_lifecycle.json

Tools specifications:
- tool_auth_user.json
- tool_define_topic_relevance.json
- tool_export_detailed_domain_snapshot.json
- tool_extract_facts_from_text.json
- tool_fetch_user_knowledge_domains.json
- tool_generate_domain_snapshot.json
- tool_prettify_domain_description.json
- tool_process_ordinary_page.json
- tool_process_pdf_link.json
- tool_process_youtube_link.json
- tool_save_fact_to_memory.json
- tool_toggle_domain_status.json

CRITICAL: In case of conflict between tool or agent specifications and a sequence diagram, the specifications take precedence.

Other docs:
- observability.md - Requirements for observability features
- high_level_test_cases.md

Ignore this files:
- combined_jsons*
- merge_jsons.sh
- '- old' directory

## Tech stack

- Python 3.13
- Google AKD (Agent Development Kit)
- Google Cloud Firestore
- Google Cloud Gemini
- Google Vertex AI

Use context7 MCP to access up-to-date documentation.

## Configuration requirements

#### 1. Prompt Management
* **Description:** Complete decoupling of logic (Code) from content (Prompts).
* **Requirement:** All text prompts, system instructions, and message templates for LLMs must be extracted to a single unified external file (e.g., `prompts.yaml`, `prompts.json`, or `prompts.py` as a dictionary of constants).
* **Goal:** To ensure the ability to edit and version prompts without modifying the source code of the business logic.

#### 2. Model Configuration Strategy
* **Description:** Centralized management of inference parameters.
* **Requirement:** Model invocation parameters (Model Name, Temperature, Top-K, Top-P, Max Output Tokens) must be stored in a separate configuration file (e.g., `config.yaml` or `models_config.json`).
* **Detailing:** The file structure must support parameter overriding for each specific component or agent in the system.
    * *Example:* The "Analyst" Agent uses `temperature=0.2`, the "Creative" Agent uses `temperature=0.9`.

#### 3. LLM Technology Stack (LLM Provider Constraint)
* **Description:** Model provider restriction.
* **Requirement:** The system must be designed exclusively to work with Google ecosystem models.
* **Permissible Models:**
    * Google Gemini (Pro, Flash, Ultra, etc.)
    * Google Gemma (open weights)

#### 4. Secrets Management
* **Description:** Standardization of sensitive data handling.
* **Requirement:** All API keys (Google AI Studio Key, Vertex AI Credentials), external service authorization keys, database tokens, and connection parameters for external MCP (Model Context Protocol) servers must be loaded exclusively from Environment Variables.
* **Implementation:** Mandatory presence of a `.env` file (included in `.gitignore`) and a `.env.example` template. Hardcoding credentials in the source code is strictly prohibited.

#### 5. Relevance treshold
The relevance treshold that used in 'subagent_document_processor' should be read from config file. Default is '0.7'.