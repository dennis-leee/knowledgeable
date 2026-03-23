"""Configuration management - single YAML config."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Model configuration."""

    summarizer: str = "gpt-4o-mini"
    extractor: str = "gpt-4o"
    embedding: str = "text-embedding-3-small"


class PipelineConfig(BaseModel):
    """Pipeline configuration."""

    max_tokens: int = 8000
    retry_limit: int = 3
    fallback_parsers: List[str] = Field(default_factory=lambda: ["jina-reader", "readability-lxml"])


class ConfidenceConfig(BaseModel):
    """Confidence threshold configuration."""

    threshold: float = 0.7
    low_confidence_action: str = "human_review"


class StorageConfig(BaseModel):
    """Storage configuration."""

    markdown_path: str = "./data/md"
    graph_path: str = "./data/graph"
    skills_path: str = "./data/skills"
    vector_store: str = "chroma"
    vector_persist: str = "./data/vectors"


class SecurityConfig(BaseModel):
    """Security configuration."""

    enabled: bool = True
    blacklist: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "harmful": ["violence", "crime", "illegal"],
            "privacy": ["pii", "personal_data"],
            "misleading": ["disinformation", "conspiracy"],
        }
    )
    action_on_match: str = "flag"


class HumanInloopConfig(BaseModel):
    """Human in-loop configuration."""

    enabled: bool = True
    pending_review_dir: str = "./pending_review"
    auto_continue_on_timeout: bool = False
    timeout_hours: int = 72


class ActiveLearningConfig(BaseModel):
    """Active learning configuration."""

    enabled: bool = False
    trigger: str = "scheduled"
    cron: str = "0 2 * * *"
    token_daily_limit: int = 100000
    require_approval: bool = True
    termination_file: str = ".stop_learning"


class SelfHealingConfig(BaseModel):
    """Self-healing configuration."""

    enabled: bool = True
    max_retries: int = 3
    external_verification: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": False,
        "trigger_threshold": 0.6,
        "provider": "duckduckgo",
    })


class Config(BaseModel):
    """Root configuration."""

    model: ModelConfig = Field(default_factory=ModelConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    confidence: ConfidenceConfig = Field(default_factory=ConfidenceConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    human_inloop: HumanInloopConfig = Field(default_factory=HumanInloopConfig)
    active_learning: ActiveLearningConfig = Field(default_factory=ActiveLearningConfig)
    self_healing: SelfHealingConfig = Field(default_factory=SelfHealingConfig)


class ConfigManager:
    """Configuration manager - single YAML file."""

    _instance: Optional["ConfigManager"] = None
    _config: Optional[Config] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: str = "app/config.yaml") -> Config:
        """Load configuration from YAML file."""
        if self._config is not None:
            return self._config

        config_file = Path(config_path)

        if not config_file.exists():
            config_file = Path(__file__).parent.parent.parent / config_path

        if not config_file.exists():
            self._config = Config()
            return self._config

        with open(config_file, "r") as f:
            data = yaml.safe_load(f) or {}

        self._config = Config.model_validate(data)
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        if self._config is None:
            self.load()

        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            elif hasattr(value, k):
                value = getattr(value, k)
            else:
                return default

            if value is None:
                return default

        return value

    def reload(self) -> Config:
        """Reload configuration from file."""
        self._config = None
        return self.load()

    def validate(self) -> bool:
        """Validate configuration."""
        if self._config is None:
            self.load()
        return self._config is not None


_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config(config_path: str = "app/config.yaml") -> Config:
    """Load configuration from file."""
    manager = get_config_manager()
    return manager.load(config_path)
