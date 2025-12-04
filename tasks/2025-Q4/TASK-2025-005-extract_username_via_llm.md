---
id: TASK-2025-005
title: "extract_username_via_llm"
type: feature
created: 2025-12-04
---

Сейчас agent_root идентифицирует имя пользователя на основе жёсткой конструкции "My name is ...". Это неудобно, т.к. навязывает пользователю английский язык и строгий формат.

Перепиши этот функционал.

# Замечание 1
Необходимо, чтобы при открытии агента, if not session_user_id, агент начинал диалог ПЕРВЫМ фразой: "Hello! Please tell me your name to get started." (эта фраза должна быть вынесена в prompts.yaml)

# Замечание 2
После того, как пользователь введёт некую строку, её необходимо обрабатывать функцией (или инструментом), которая обратится к LLM, чтобы извлечь из строки имя пользователя.
Модель - дефолтная, установленная в конфиге.

## ПРОМПТ для извлечения имени пользователя (должен быть вынесен в prompts.yaml)

```
You are a name extraction assistant. Your task is to identify the user's name from their message.

Instructions:
1. Extract the person's first name (and optionally last name) from the user's input
2. The user may write in any language (English, Russian, Spanish, Chinese, Arabic, etc.)
3. The name may be introduced in various ways: "I'm John", "Меня зовут Иван", "Je m'appelle Marie", "我叫李明", etc.
4. Return ONLY a JSON object in the following format:

{"name": "<extracted_name>", "confidence": "high|medium|low", "detected": true|false}

If no name is found, return:
{"name": null, "confidence": null, "detected": false}

Examples:

Input: "Привет, я Алексей"
Output: {{"name": "Алексей", "confidence": "high", "detected": true}}

Input: "Hello there!"
Output: {{"name": null, "confidence": null, "detected": false}}

Input: "My name is Sarah Chen"
Output: {{"name": "Sarah Chen", "confidence": "high", "detected": true}}

User message: {user_input}
```

Имя - non-case-sensitive.

Если имя не определено, необходимо сообщить пользователю об ошибке и попросить повторно ввести имя. Максимальное количество попыток за сессию - 3. Когда оно достигнуто, сообщить пользователю, что доступ запрещён, предложить пользователю попросить новую сессию.

Если имя определено, применяем текущую логику:
- получаем user_id из базы, либо создаём новый user_id
- получаем список доменов, сообщаем о них пользователю
- и т.д.

# Замечание 3
Создай тесты для проверки этой функциональности.

# Замечание 4
Процесс получения строки от пользователя, обработки в LLM и получения имени, проверки в базе пользователей и успешной/неуспешной аутентификации должен быть обложен трейсингом.

Задай мне вопросы, если что-то требуется уточнить.