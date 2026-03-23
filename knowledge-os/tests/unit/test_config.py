"""Unit tests for config management."""

import tempfile
from pathlib import Path

import pytest

from app.config import Config, ConfigManager, load_config


class TestConfigManager:
    """Tests for ConfigManager."""

    @pytest.fixture
    def config_file(self):
        """Create temporary config file."""
        config_content = """
model:
  summarizer: "gpt-4o-mini"
  extractor: "gpt-4o"
  embedding: "text-embedding-3-small"

pipeline:
  max_tokens: 8000
  retry_limit: 3

confidence:
  threshold: 0.7
  low_confidence_action: "human_review"

storage:
  markdown_path: "./data/md"
  graph_path: "./data/graph"
  skills_path: "./data/skills"
  vector_store: "chroma"
  vector_persist: "./data/vectors"

security:
  enabled: true
  blacklist:
    harmful: ["violence", "crime"]
  action_on_match: "flag"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            yield f.name
        Path(f.name).unlink(missing_ok=True)

    def test_load_config(self, config_file):
        """Test loading configuration from file."""
        manager = ConfigManager()
        config = manager.load(config_file)
        assert config is not None
        assert config.model.summarizer == "gpt-4o-mini"
        assert config.pipeline.max_tokens == 8000
        assert config.confidence.threshold == 0.7

    def test_get_with_dot_notation(self, config_file):
        """Test getting nested config values."""
        manager = ConfigManager()
        manager.load(config_file)
        
        assert manager.get("model.summarizer") == "gpt-4o-mini"
        assert manager.get("pipeline.retry_limit") == 3
        assert manager.get("nonexistent.key", "default") == "default"

    def test_get_default_value(self, config_file):
        """Test getting default value for missing key."""
        manager = ConfigManager()
        manager.load(config_file)
        
        assert manager.get("nonexistent") is None
        assert manager.get("nonexistent", "default") == "default"

    def test_reload_config(self, config_file):
        """Test reloading configuration."""
        manager = ConfigManager()
        manager.load(config_file)
        first_load = manager.get("model.summarizer")
        
        manager.reload()
        second_load = manager.get("model.summarizer")
        
        assert first_load == second_load

    def test_validate_config(self, config_file):
        """Test configuration validation."""
        manager = ConfigManager()
        manager.load(config_file)
        assert manager.validate() is True


class TestConfigModel:
    """Tests for Config model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        assert config.model.summarizer == "gpt-4o-mini"
        assert config.pipeline.max_tokens == 8000
        assert config.pipeline.retry_limit == 3
        assert config.confidence.threshold == 0.7
        assert config.security.enabled is True

    def test_config_serialization(self):
        """Test config to dict."""
        config = Config()
        data = config.model_dump()
        assert "model" in data
        assert "pipeline" in data
