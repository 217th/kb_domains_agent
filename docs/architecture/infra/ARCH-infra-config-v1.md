---
id: ARCH-infra-config
title: "Infrastructure: Configuration & Prompts"
type: component
layer: infrastructure
owner: @team-platform
version: v1
status: current
created: 2025-12-02
updated: 2025-12-02
tags: [config, env, prompts]
depends_on: []
referenced_by: []
---
## Context
Centralized configuration management for the application, handling environment variables, model configurations, and externalized prompts.

## Structure
*   **File:** `src/utils/config_loader.py`
*   **Config Files:**
    *   `config/config.yaml`: Model parameters (temperature, tokens) and thresholds.
    *   `config/prompts.yaml`: System prompts for agents.
    *   `.env`: Secrets and feature flags.

## Behavior
*   **Singleton Pattern:** `ConfigLoader` ensures configs are loaded once.
*   **Validation:** Uses `pydantic-settings` to validate environment variables.
*   **Prompt Management:** Decouples logic from text by loading prompts from YAML.
*   **Model Config:** Allows per-component overrides for LLM parameters.

## Evolution
### Historical
*   v1: Initial setup with Pydantic settings and YAML-based prompt/config loading.
