# Observability Requirements Document v2.0

Функции Observability должны быть реализованы с использованием:
- Google Cloud Monitoring (https://docs.cloud.google.com/monitoring/docs)
- Google Cloud Logging (https://docs.cloud.google.com/logging/docs)
- Google Cloud Trace (https://docs.cloud.google.com/trace/docs)

## SECTION 1: Trace Instrumentation Requirements (Cloud Trace)

### 1.1 Trace Span Map (Карта спанов)

*Жирным выделены новые или измененные требования.*

| Interaction Step | Span Name | Attributes to Capture (Metadata) | Criticality |
| :--- | :--- | :--- | :--- |
| **Incoming Request** | `root_agent_turn` | `user_id`, `session_id` | Critical |
| **Delegation** | `agent_handoff` | `source`, `target`, **`model_config_id`** (из `AGENTS.md`) | Critical |
| **Domain Fetch** | `firestore_fetch_domains` | `user_id`, `count`, `view_mode` | Medium |
| **Doc Processing** | `subagent_doc_proc_turn` | `input_url`, `detected_type` | High |
| **Relevance Loop** | `eval_domain_relevance` | `domain_name`, `score`, **`threshold_used`** | Low (High Vol.) |
| **Fact Extraction** | `llm_fact_extraction` | `fact_count`, **`prompt_version_hash`** | High |
| **Fact Save Loop** | **`save_facts_batch`** | `total_facts_selected` | Medium |
| **Single Fact Save**| **`tool_save_fact_to_memory`**| `domain_id`, `memory_id` (result) | **Critical** |

### 1.2 Context Propagation & Config Tracking

  * **Prompt/Config Versioning:** Поскольку промпты и конфиги моделей теперь внешние (`prompts.yaml`, `config.yaml`), каждый Span, связанный с вызовом LLM (`agent_root`, `subagent_*`), **ОБЯЗАН** содержать атрибут `config_version` или хеш загруженного промпта. Это единственный способ понять, почему вчера агент отвечал иначе, чем сегодня, если код не менялся.
  * **Trace ID in Loops:** В цикле сохранения фактов (`tool_save_fact_to_memory`) каждый вызов инструмента должен быть дочерним спаном родительского спана `save_facts_batch`.

-----

## SECTION 2: Logging & Data Masking Policy (Cloud Logging)

### 2.1 Standard Log Entry Schema (Updates)

В структуру лога необходимо добавить поля для отладки конфигураций.

```json
{
  "severity": "INFO",
  "component": "subagent_document_processor",
  "trace_id": "projects/my-project/traces/...",
  "labels": {
    "agent_version": "v1.0.2",
    "prompt_version_sha": "a1b2c3d",   // <-- NEW: Требование AGENTS.md
    "model_config_profile": "analyst_strict" // <-- NEW: Профиль из config.yaml
  },
  "jsonPayload": {
    "event_type": "RELEVANCE_CHECK",
    "domain": "AI Trends",
    "relevance_score": 0.65,
    "relevance_threshold": 0.7,        // <-- NEW: Важно для отладки отсечения
    "verdict": "DROPPED"
  }
}
```

### 2.2 Data Masking (Privacy)

С учетом новых файлов:

1.  **`tool_save_fact_to_memory`**:
      * Поле `fact_text`: Может содержать чувствительные данные. **Log Policy:** Truncate до 200 символов в логах уровня `INFO`. Полный текст только в `DEBUG` (отключено в проде).
      * Поле `user_id`: Хэшировать в логах, если это PII (email/телефон), или оставлять как есть, если это UUID.
2.  **Secrets (`AGENTS.md` Reqs):**
      * При старте приложения, если логируется загруженная конфигурация, **СТРОГО ФИЛЬТРОВАТЬ** ключи, содержащие `KEY`, `TOKEN`, `CREDENTIALS`, `SECRET` (в соответствии с требованием `.env`).

-----

## SECTION 3: Metrics & KPIs (Cloud Monitoring)

### 3.1 New Operational Metrics

| Metric Name | Type | Source | Alert Threshold | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`mas/fact_save_latency`** | Distribution | `tool_save_fact_to_memory` | \> 2000ms (p95) | Время записи одного факта в Memory Bank. |
| **`mas/fact_save_batch_size`** | Distribution | `subagent_document_processor` | N/A | Сколько фактов пользователи сохраняют за раз (для capacity planning). |
| **`mas/config_reload_count`** | Counter | App Init | \> 0 | Отслеживание перезагрузок конфигураций/промптов. |

### 3.2 Business Metrics (Derived from Logs)

1.  **Acceptance Rate (User Feedback):**
      * *Formula:* `facts_saved_count / facts_extracted_count`
      * *Meaning:* Насколько качественно агент извлекает факты. Если пользователь сохраняет 0 из 10 предложенных — промпт извлечения или порог релевантности требуют тюнинга.
2.  **Relevance Threshold Effectiveness:**
      * Гистограмма `relevance_score` для всех проверок. Если распределение смещено к 0.99 или 0.01, порог 0.7 (из `AGENTS.md`) неэффективен.

-----

## SECTION 4: Alerting Thresholds (Updated)

1.  **Memory Bank Write Failure (Critical):**
      * **Condition:** `rate(mas/tool_error_rate{tool="tool_save_fact_to_memory"}) > 0` (Любая ошибка записи недопустима, так как это потеря пользовательских данных).
      * **Action:** PagerDuty / Urgent Notification.
2.  **Configuration Error:**
      * **Condition:** Логи содержат `LLM_AUTH_ERROR` или ошибки парсинга `prompts.yaml`.
      * **Action:** Блокирующий алерт (система неработоспособна).
3.  **Low Relevance Intake:**
      * **Condition:** Агент обрабатывает \> 100 ссылок, но `saved_count` == 0 за последние 24 часа.
      * **Meaning:** Возможно, сломалась логика классификации или `tool_process_*` возвращают пустой текст.

## Рекомендация по внедрению

В соответствии с `AGENTS.md`, начните с создания `observability_config.yaml`, где будут определены sampling rates и правила маскирования, чтобы отделить настройки мониторинга от кода агентов.