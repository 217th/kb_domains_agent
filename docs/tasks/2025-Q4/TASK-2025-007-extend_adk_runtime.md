---
id: TASK-2025-007
title: "extend_adk_runtime"
type: rework
---

# Documentation

Используй web_search_request и используй документацию:
  https://google.github.io/adk-docs/runtime/
  https://google.github.io/adk-docs/runtime/runconfig/
  https://google.github.io/adk-docs/get-started/python/

# Implementation plan
1. Baseline & inventory
   - Catalog existing agents/subagents/tools, prompts, env flags (RUN_REAL_AI, RUN_REAL_MEMORY, ENABLE_GCP_LOGGING, relevance threshold) and session fields (user_id, user_name, name_attempts, intent/url/domain_id). Зафиксировать, что бизнес-логика должна сохраниться без изменений.

2. ADK scaffold without regression
   - Добавить `agent.py` с декларативными ADK Agent-объявлениями для root и обоих сабагентов, с биндингами существующих tool функций. Сохранить старые реализации как внутреннюю бизнес-логику, вызываемую из обёрток.

3. Runner + RunConfig
   - Ввести инициализацию ADK Runner; завести RunConfig профили (dev/mock, prod/real), которые мапят текущие env-флаги на поля RunConfig (streaming/off, artifact saving, max_llm_calls, tracing).
   - Прокинуть выбор профиля из CLI/Web (параметр или env) в Runner.

4. ADK SessionService
   - Заменить кастомный session manager на встроенный SessionService (InMemorySessionService), серверная генерация session_id на первом запросе.
   - Переместить state-поля (user_id, user_name, name_attempts, intent/url/domain_id) в SessionService; убрать их передачу через payload, оставив временный шим совместимости.

5. Перепись агентов под event-stream
   - Превратить функции агентов в генераторы, yieldящие ADK Events (messages, tool calls, state updates) вместо возврата dict. Делегации оформлять как вложенные вызовы child agent, а не прямые функции.
   - Сохранить все ветки бизнес-логики и проверки доменов/URL, превратив текущие tool-вызовы в события.

6. Наблюдаемость через ADK
   - Включить встроенный логгинг/Cloud Trace ADK, добавить session_id в trace атрибуты/префиксы. Перенести причины hand-off в labels событий. После проверки parity минимизировать/убрать кастомный telemetry.

7. Entry points через ADK
   - Добавить конфигурацию для `adk run` и `adk web`; CLI-обёртка должна вызывать Runner. Web заменить на ADK web UI/endpoint; legacy FastAPI держать под фичефлагом до стабилизации.

8. Совместимость инструментов и данных
   - Убедиться, что Firestore/Gemini/моки работают под Runner; флаги RUN_REAL_AI/RUN_REAL_MEMORY интегрировать в RunConfig. Схемы коллекций не менять.

9. Тестирование
   - Обновить unit/e2e тесты под Runner+SessionService: hand-off состояния, name extraction, доменный цикл, обработка URL. Прогнать интеграцию с реальным Firestore в prod профиле.

10. Документация и .env
    - Обновить README и `.env.example` новыми командами (`adk run`, `adk web`), описанием RunConfig профилей и обязательных переменных. Добавить заметку о миграции с legacy оркестрации.

11. Cutover
    - По умолчанию переключить entrypoints на ADK после успешных тестов; оставить предупреждение в legacy путях и удалить их после окна стабилизации.
