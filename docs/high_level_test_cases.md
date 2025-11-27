#### 1\. Functional & Logic Tests (Core Workflow)

| ID | Component | Scope / Description | Criticality |
| :--- | :--- | :--- | :--- |
| **T-01** | `agent_root` | [cite\_start]**Routing Logic.** Проверка маршрутизации: URL → `subagent_document_processor`, команды создания/правки → `subagent_domain_lifecycle` [cite: 156-158]. | **Critical** |
| **T-02** | `agent_root` / `tool_auth_user` | **Authentication Flow.** Если `session_user_id` отсутствует, агент должен извлечь имя и вызвать `tool_auth_user`. [cite\_start]Если имя не найдено — запросить ввод [cite: 153-155]. | **High** |
| **T-03** | `subagent_domain_lifecycle` | **Confirmation Loop.** Агент **не** должен сохранять домен в Firestore, пока `confirmation_status` в input равен `false`. [cite\_start]Должен возвращать статус `AWAITING_USER_REVIEW` [cite: 213-214, 221]. | **Critical** |
| **T-04** | `subagent_document_processor` | [cite\_start]**URL Heuristics.** Проверка классификации URL (PDF vs YouTube vs Web) на основе строковых паттернов (regex) перед вызовом инструментов [cite: 178-180]. | **High** |
| **T-05** | `subagent_document_processor` | [cite\_start]**Review Handoff Contract.** Проверка схемы выхода `candidate_facts`: обязательное наличие полей `fact_id`, `content`, `domain_id` и **`source_url`** для передачи в следующий шаг [cite: 185, 201-204]. | **High** |
| **T-06** | `subagent_document_processor` <br> `tool_save_fact_to_memory` | **Batch Save Loop.** (Integration) Симуляция выбора N фактов пользователем. [cite\_start]Проверка, что агент вызывает `tool_save_fact_to_memory` ровно N раз с корректным маппингом (`payload.content` -\> `fact_text`)[cite: 187, 295]. | **Critical** |
| **T-07** | `tool_save_fact_to_memory` | [cite\_start]**Atomic Write.** (Unit) Проверка вызова инструмента: валидация входных полей (`user_id`, `domain_id`, `source_url`) и корректный возврат `memory_id` при успехе [cite: 295-302]. | **High** |
| **T-08** | `agent_root` | [cite\_start]**Error Translation.** Проверка перехвата технических ошибок (напр., `FIRESTORE_UNAVAILABLE`) и их преобразования в дружелюбные сообщения для пользователя[cite: 161]. | **Medium** |

#### 2\. AI Quality & Semantic Tests (Model-Based Eval)

| ID | Component | Scope / Description | Eval Method |
| :--- | :--- | :--- | :--- |
| **T-09** | `tool_prettify_domain_description` | [cite\_start]**Domain Structure.** Проверка, что "сырой" текст пользователя преобразуется в формальное `description` и список релевантных `keywords`, а не просто копируется[cite: 274]. | **Rubric** |
| **T-10** | `tool_define_topic_relevance` | **Relevance Threshold.** Подача заведомо нерелевантного текста для домена. [cite\_start]Ожидается `relevance_score` ниже порогового значения (default 0.7) [cite: 183, 233-236]. | **Golden Dataset** |
| **T-11** | `tool_extract_facts_from_text` | **Fact Atomicity.** Проверка, что из текста извлекаются отдельные факты (атомарные утверждения), а не один большой суммаризированный абзац. [cite\_start]Проверка уникальности `fact_id`[cite: 250]. | **Rubric** |

#### 3\. Non-Functional: Observability & Config (New Requirements)

| ID | Component | Scope / Description | Criticality |
| :--- | :--- | :--- | :--- |
| **T-12** | `System / Logging` | **Data Masking (Privacy).** Проверка логов при сохранении факта. Поле `fact_text` в логах уровня INFO должно быть обрезано до 200 символов. | **High** |
| **T-13** | `System / Tracing` | **Config Versioning.** Проверка Trace Spans: каждый вызов LLM агента должен содержать атрибут `prompt_version_hash` или `model_config_id`. | **Medium** |
| **T-14** | `System / Tracing` | **Trace Context Propagation.** Проверка, что вызовы `tool_save_fact_to_memory` являются дочерними спанами (children) по отношению к родительскому спану `save_facts_batch`. | **Low** |
| **T-15** | `Infrastructure` | **Secrets Management.** Проверка запуска без `.env` файла. Система должна аварийно завершаться, не пытаясь использовать дефолтные ключи. | **High** |
| **T-16** | `Monitoring` | **Performance Alert.** Искусственная задержка ответа Memory Bank (\>2s). Проверка срабатывания метрики/алерта `mas/fact_save_latency`. | **Low** |