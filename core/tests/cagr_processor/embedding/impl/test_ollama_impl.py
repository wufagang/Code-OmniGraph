"""OllamaEmbedding 单元测试（全部使用 mock，不依赖本地 Ollama 服务）"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from urllib.error import URLError

from cagr_common.exceptions import (
    EmbeddingConfigException,
    EmbeddingConnectionException,
    EmbeddingTimeoutException,
)
from cagr_processor.embedding.config import EmbeddingConfig, OllamaEmbeddingConfig


def _make_config(**kwargs) -> EmbeddingConfig:
    defaults = {"host": "localhost", "port": 11434, "model": "nomic-embed-text"}
    defaults.update(kwargs)
    return EmbeddingConfig(
        provider="ollama",
        ollama_config=OllamaEmbeddingConfig(**defaults),
    )


class TestOllamaEmbeddingViaSdk:
    @patch("cagr_processor.embedding.impl.ollama_impl.OLLAMA_SDK_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.ollama_impl._ollama")
    def test_embed_via_sdk(self, mock_ollama):
        mock_client = Mock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_ollama.Client.return_value = mock_client

        from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
        model = OllamaEmbedding(_make_config())
        result = model.embed("public void foo() {}")

        assert result == [0.1, 0.2, 0.3]
        mock_client.embeddings.assert_called_once_with(
            model="nomic-embed-text", prompt="public void foo() {}"
        )

    @patch("cagr_processor.embedding.impl.ollama_impl.OLLAMA_SDK_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.ollama_impl._ollama")
    def test_sdk_error_wrapped(self, mock_ollama):
        mock_ollama.Client.return_value.embeddings.side_effect = Exception("sdk error")

        from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
        model = OllamaEmbedding(_make_config())
        with pytest.raises(EmbeddingConnectionException):
            model.embed("text")


class TestOllamaEmbeddingViaHttp:
    @patch("cagr_processor.embedding.impl.ollama_impl.OLLAMA_SDK_AVAILABLE", False)
    @patch("cagr_processor.embedding.impl.ollama_impl.urllib.request.urlopen")
    def test_embed_via_http(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"embedding": [0.4, 0.5]}).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
        model = OllamaEmbedding(_make_config())
        result = model.embed("some code")

        assert result == [0.4, 0.5]

    @patch("cagr_processor.embedding.impl.ollama_impl.OLLAMA_SDK_AVAILABLE", False)
    @patch("cagr_processor.embedding.impl.ollama_impl.urllib.request.urlopen")
    def test_timeout_raises_correct_exception(self, mock_urlopen):
        err = URLError("timed out")
        err.reason = "timed out"
        mock_urlopen.side_effect = err

        from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
        model = OllamaEmbedding(_make_config())
        with pytest.raises(EmbeddingTimeoutException):
            model.embed("text")

    @patch("cagr_processor.embedding.impl.ollama_impl.OLLAMA_SDK_AVAILABLE", False)
    @patch("cagr_processor.embedding.impl.ollama_impl.urllib.request.urlopen")
    def test_connection_error_raises_correct_exception(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("connection refused")

        from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
        model = OllamaEmbedding(_make_config())
        with pytest.raises(EmbeddingConnectionException):
            model.embed("text")


class TestOllamaEmbeddingMeta:
    @patch("cagr_processor.embedding.impl.ollama_impl.OLLAMA_SDK_AVAILABLE", False)
    def test_detect_dimension_known_model(self):
        from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
        model = OllamaEmbedding(_make_config(model="nomic-embed-text"))
        assert model.detectDimension() == 768

    @patch("cagr_processor.embedding.impl.ollama_impl.OLLAMA_SDK_AVAILABLE", False)
    def test_detect_dimension_unknown_model_defaults_768(self):
        from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
        model = OllamaEmbedding(_make_config(model="custom-model-xyz"))
        assert model.detectDimension() == 768

    @patch("cagr_processor.embedding.impl.ollama_impl.OLLAMA_SDK_AVAILABLE", False)
    def test_detect_dimension_mxbai(self):
        from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
        model = OllamaEmbedding(_make_config(model="mxbai-embed-large"))
        assert model.detectDimension() == 1024

    @patch("cagr_processor.embedding.impl.ollama_impl.OLLAMA_SDK_AVAILABLE", False)
    def test_get_provider(self):
        from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
        model = OllamaEmbedding(_make_config())
        assert model.getProvider() == "ollama"

    @patch("cagr_processor.embedding.impl.ollama_impl.OLLAMA_SDK_AVAILABLE", False)
    def test_missing_ollama_config_raises(self):
        cfg = EmbeddingConfig(provider="ollama")
        from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
        with pytest.raises(EmbeddingConfigException):
            OllamaEmbedding(cfg)
