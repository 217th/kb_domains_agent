---
id: TASK-2025-
title: "fix_domain_confirmation_logic"
type: feature
---

Сейчас:
- run_subagent_domain_lifecycle вызывает tool_prettify_domain_description, получает оттуда draft, показывает его пользователю
- обработка подтверждения от пользователя (confirm и т.д.) происходит в chat.py

Необходимо вернуть её полностью в run_subagent_domain_lifecycle, включить в сообщения пользователю опции (y/n/cancel). В зависимости от этого, выполнять обработку.