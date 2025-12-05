# AGENTS.md

## `docs` directory
Contains project and system design artifacts of a multi-agent system using Google ADK.

- `docs/project_overview.md` - If I were you, I'd start with this file. Then I'd delve into sequence diagram and specifications of each component.
- `docs/sequence_diagram.md` - Mermaid sequence diagram showing key interactions between agents/subagents, tools and external resources.
- `docs/architecture` - Directory with detailed specs for infrastructure services, AI-agents/subagents, tools/services.
- `docs/tasks` - Directory with artifacts of implementation plan. IGNORE THIS until I give you an EXPLICIT COMMAND to implement specific tasks.
- `docs/- old` - IGNORE THIS

CRITICAL: In case of conflict between tool or agent specifications and a sequence diagram, the specifications take precedence.

## Tech stack

- Python 3.13
- Google ADK (Agent Development Kit)
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

## Docstrings

Write and keep up-to-date a module-level docstring for each Python file. Include the following:
- A concise summary of the module’s purpose and context (1–2 sentences: what this module does, in what context it is used).
- A list of main public objects: key classes, functions, and exceptions with a very brief explanation of each (especially important for library code).
- Add:
    - Information about usage examples, environment settings, or global variables.
    - Links to more detailed documentation or specifications.
    - Warnings or limitations (such as if an API is experimental).

The docstring should follow PEP 257 style guidelines: use triple double quotes, start with a short summary, and structure any further details in new paragraphs. Use clear, concise language suitable for users of your module.
