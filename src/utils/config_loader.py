from __future__ import annotations

"""
Config loader responsible for:
- Validating required env vars via pydantic settings (.env).
- Loading prompts/config YAML.
- Exposing helpers for model configs and thresholds.
"""

import os
from pathlib import Path
from typing import Any, ClassVar, Dict

import yaml
from dotenv import load_dotenv
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_RELEVANCE_THRESHOLD = 0.7


class EnvSettings(BaseSettings):
    google_application_credentials: str = Field(..., alias="GOOGLE_APPLICATION_CREDENTIALS")
    google_cloud_project: str = Field(..., alias="GOOGLE_CLOUD_PROJECT")
    google_api_key: str | None = Field(None, alias="GOOGLE_API_KEY")
    firestore_database: str | None = Field("(default)", alias="FIRESTORE_DATABASE")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ConfigLoader:
    _instance: ClassVar["ConfigLoader" | None] = None

    def __init__(self) -> None:
        env_path = BASE_DIR / ".env"
        load_dotenv(dotenv_path=env_path)
        missing = [name for name in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT") if not os.getenv(name)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
        try:
            self.settings = EnvSettings()  # type: ignore[arg-type]
        except ValidationError as exc:
            raise EnvironmentError(f"Invalid environment configuration: {exc}") from exc
        self.prompts = self._load_yaml(BASE_DIR / "config" / "prompts.yaml")
        self.config = self._load_yaml(BASE_DIR / "config" / "config.yaml")

    @classmethod
    def instance(cls) -> "ConfigLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def _load_yaml(path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_prompt(self, agent_id: str) -> str:
        prompt = self.prompts.get(agent_id)
        if not isinstance(prompt, str):
            raise KeyError(f"No prompt configured for agent_id='{agent_id}'")
        return prompt

    def get_model_config(self, component_id: str) -> Dict[str, Any]:
        model_config = self.config.get("model_config", {})
        default_cfg = model_config.get("default", {}) or {}
        overrides = model_config.get("overrides", {}).get(component_id, {}) or {}
        merged = {**default_cfg, **overrides}
        if "model_id" not in merged:
            raise KeyError(f"Model configuration missing required 'model_id' for component '{component_id}'")
        return merged

    def get_relevance_threshold(self, component_id: str) -> float:
        thresholds = self.config.get("thresholds", {})
        component_threshold = thresholds.get(component_id, {})
        value = component_threshold.get("relevance", DEFAULT_RELEVANCE_THRESHOLD)
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid relevance threshold for '{component_id}': {value}") from exc


def load_prompts() -> Dict[str, str]:
    return ConfigLoader.instance().prompts


def load_model_config(component_id: str) -> Dict[str, Any]:
    return ConfigLoader.instance().get_model_config(component_id)


def load_relevance_threshold(component_id: str) -> float:
    return ConfigLoader.instance().get_relevance_threshold(component_id)
