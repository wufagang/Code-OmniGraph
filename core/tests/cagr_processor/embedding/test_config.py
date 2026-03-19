import os
import pytest
from unittest.mock import patch

from cagr_common.exceptions import EmbeddingConfigException
from cagr_processor.embedding.config import (
    EmbeddingConfig,
    OpenAIEmbeddingConfig,
    GeminiEmbeddingConfig,
    OllamaEmbeddingConfig,
)


class TestOpenAIEmbeddingConfig:
    def test_defaults(self):
        cfg = OpenAIEmbeddingConfig()
        assert cfg.model == "text-embedding-3-small"
        assert cfg.timeout == 30.0
        assert cfg.max_tokens == 8191
        assert cfg.base_url is None

    def test_custom(self):
        cfg = OpenAIEmbeddingConfig(api_key="sk-x", model="text-embedding-3-large", base_url="http://proxy")
        assert cfg.api_key == "sk-x"
        assert cfg.model == "text-embedding-3-large"
        assert cfg.base_url == "http://proxy"


class TestGeminiEmbeddingConfig:
    def test_defaults(self):
        cfg = GeminiEmbeddingConfig()
        assert cfg.model == "models/text-embedding-004"
        assert cfg.task_type == "RETRIEVAL_DOCUMENT"
        assert cfg.max_tokens == 2048

    def test_custom(self):
        cfg = GeminiEmbeddingConfig(api_key="gm-k", model="models/embedding-001")
        assert cfg.api_key == "gm-k"
        assert cfg.model == "models/embedding-001"


class TestOllamaEmbeddingConfig:
    def test_defaults(self):
        cfg = OllamaEmbeddingConfig()
        assert cfg.host == "localhost"
        assert cfg.port == 11434
        assert cfg.model == "nomic-embed-text"
        assert cfg.max_tokens == 8192


class TestEmbeddingConfigValidate:
    def test_valid_openai(self):
        cfg = EmbeddingConfig(provider="openai", openai_config=OpenAIEmbeddingConfig())
        cfg.validate()  # no exception

    def test_valid_gemini(self):
        cfg = EmbeddingConfig(provider="gemini", gemini_config=GeminiEmbeddingConfig())
        cfg.validate()

    def test_valid_ollama(self):
        cfg = EmbeddingConfig(provider="ollama", ollama_config=OllamaEmbeddingConfig())
        cfg.validate()

    def test_missing_openai_config(self):
        cfg = EmbeddingConfig(provider="openai")
        with pytest.raises(EmbeddingConfigException):
            cfg.validate()

    def test_missing_gemini_config(self):
        cfg = EmbeddingConfig(provider="gemini")
        with pytest.raises(EmbeddingConfigException):
            cfg.validate()

    def test_missing_ollama_config(self):
        cfg = EmbeddingConfig(provider="ollama")
        with pytest.raises(EmbeddingConfigException):
            cfg.validate()

    def test_unsupported_provider(self):
        cfg = EmbeddingConfig(provider="unknown")
        with pytest.raises(EmbeddingConfigException):
            cfg.validate()

    def test_invalid_batch_size(self):
        cfg = EmbeddingConfig(
            provider="openai",
            openai_config=OpenAIEmbeddingConfig(),
            batch_size=0,
        )
        with pytest.raises(EmbeddingConfigException):
            cfg.validate()


class TestEmbeddingConfigFromEnv:
    def test_from_env_openai(self):
        env = {"EMBEDDING_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}
        with patch.dict(os.environ, env):
            cfg = EmbeddingConfig.from_env()
        assert cfg.provider == "openai"
        assert cfg.openai_config.api_key == "sk-test"
        assert cfg.openai_config.model == "text-embedding-3-small"

    def test_from_env_openai_custom_model(self):
        env = {
            "EMBEDDING_PROVIDER": "openai",
            "OPENAI_API_KEY": "key",
            "OPENAI_EMBEDDING_MODEL": "text-embedding-3-large",
            "OPENAI_API_BASE": "http://proxy.example.com",
        }
        with patch.dict(os.environ, env):
            cfg = EmbeddingConfig.from_env()
        assert cfg.openai_config.model == "text-embedding-3-large"
        assert cfg.openai_config.base_url == "http://proxy.example.com"

    def test_from_env_gemini(self):
        env = {"EMBEDDING_PROVIDER": "gemini", "GEMINI_API_KEY": "gm-key"}
        with patch.dict(os.environ, env):
            cfg = EmbeddingConfig.from_env()
        assert cfg.provider == "gemini"
        assert cfg.gemini_config.api_key == "gm-key"

    def test_from_env_ollama(self):
        env = {
            "EMBEDDING_PROVIDER": "ollama",
            "OLLAMA_HOST": "192.168.1.1",
            "OLLAMA_PORT": "11435",
            "OLLAMA_EMBEDDING_MODEL": "bge-m3",
        }
        with patch.dict(os.environ, env):
            cfg = EmbeddingConfig.from_env()
        assert cfg.provider == "ollama"
        assert cfg.ollama_config.host == "192.168.1.1"
        assert cfg.ollama_config.port == 11435
        assert cfg.ollama_config.model == "bge-m3"

    def test_from_env_default_is_openai(self):
        with patch.dict(os.environ, {}, clear=True):
            cfg = EmbeddingConfig.from_env()
        assert cfg.provider == "openai"

    def test_from_env_unsupported_provider(self):
        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "unknown_db"}):
            with pytest.raises(EmbeddingConfigException):
                EmbeddingConfig.from_env()

    def test_from_env_batch_size(self):
        env = {"EMBEDDING_PROVIDER": "openai", "EMBEDDING_BATCH_SIZE": "50"}
        with patch.dict(os.environ, env):
            cfg = EmbeddingConfig.from_env()
        assert cfg.batch_size == 50
