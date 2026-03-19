"""OpenAIEmbedding 单元测试（全部使用 mock，不调用真实 API）"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from cagr_common.exceptions import (
    EmbeddingConnectionException,
    EmbeddingConfigException,
    EmbeddingRateLimitException,
    EmbeddingTimeoutException,
)
from cagr_processor.embedding.config import EmbeddingConfig, OpenAIEmbeddingConfig


def _make_config(**kwargs) -> EmbeddingConfig:
    defaults = {"api_key": "sk-test", "model": "text-embedding-3-small"}
    defaults.update(kwargs)
    return EmbeddingConfig(
        provider="openai",
        openai_config=OpenAIEmbeddingConfig(**defaults),
    )


class TestOpenAIEmbedding:
    @patch("cagr_processor.embedding.impl.openai_impl.OPENAI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.openai_impl._openai")
    def test_embed_returns_vector(self, mock_openai):
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_openai.OpenAI.return_value.embeddings.create.return_value = mock_response

        from cagr_processor.embedding.impl.openai_impl import OpenAIEmbedding
        model = OpenAIEmbedding(_make_config())
        result = model.embed("hello world")

        assert result == [0.1, 0.2, 0.3]
        mock_openai.OpenAI.return_value.embeddings.create.assert_called_once()

    @patch("cagr_processor.embedding.impl.openai_impl.OPENAI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.openai_impl._openai")
    def test_embed_preprocesses_text(self, mock_openai):
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.5])]
        mock_client = mock_openai.OpenAI.return_value
        mock_client.embeddings.create.return_value = mock_response

        from cagr_processor.embedding.impl.openai_impl import OpenAIEmbedding
        model = OpenAIEmbedding(_make_config())
        model.embed("  text with spaces  ")

        call_kwargs = mock_client.embeddings.create.call_args[1]
        assert call_kwargs["input"] == "text with spaces"

    @patch("cagr_processor.embedding.impl.openai_impl.OPENAI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.openai_impl._openai")
    def test_rate_limit_raises_correct_exception(self, mock_openai):
        mock_openai.RateLimitError = type("RateLimitError", (Exception,), {})
        mock_openai.APITimeoutError = type("APITimeoutError", (Exception,), {})
        mock_openai.APIConnectionError = type("APIConnectionError", (Exception,), {})
        mock_openai.OpenAI.return_value.embeddings.create.side_effect = mock_openai.RateLimitError("rate limit")

        from importlib import reload
        import cagr_processor.embedding.impl.openai_impl as m
        reload(m)

        from cagr_processor.embedding.impl.openai_impl import OpenAIEmbedding
        with patch.object(m, "_openai", mock_openai), patch.object(m, "OPENAI_AVAILABLE", True):
            model = OpenAIEmbedding.__new__(OpenAIEmbedding)
            model.config = _make_config()
            model._client = mock_openai.OpenAI.return_value
            model._model = "text-embedding-3-small"
            model._dimension = None

            with pytest.raises(EmbeddingRateLimitException):
                model.embed("text")

    @patch("cagr_processor.embedding.impl.openai_impl.OPENAI_AVAILABLE", False)
    def test_raises_config_exception_when_sdk_missing(self):
        from cagr_processor.embedding.impl.openai_impl import OpenAIEmbedding
        with pytest.raises(EmbeddingConfigException, match="openai package"):
            OpenAIEmbedding(_make_config())

    @patch("cagr_processor.embedding.impl.openai_impl.OPENAI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.openai_impl._openai")
    def test_detect_dimension_from_map(self, mock_openai):
        mock_openai.OpenAI.return_value.embeddings = Mock()
        from cagr_processor.embedding.impl.openai_impl import OpenAIEmbedding
        model = OpenAIEmbedding(_make_config(model="text-embedding-3-large"))
        assert model.detectDimension() == 3072

    @patch("cagr_processor.embedding.impl.openai_impl.OPENAI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.openai_impl._openai")
    def test_get_dimension_cached(self, mock_openai):
        mock_openai.OpenAI.return_value.embeddings = Mock()
        from cagr_processor.embedding.impl.openai_impl import OpenAIEmbedding
        model = OpenAIEmbedding(_make_config())
        d1 = model.getDimension()
        d2 = model.getDimension()
        assert d1 == d2 == 1536

    @patch("cagr_processor.embedding.impl.openai_impl.OPENAI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.openai_impl._openai")
    def test_get_provider(self, mock_openai):
        mock_openai.OpenAI.return_value.embeddings = Mock()
        from cagr_processor.embedding.impl.openai_impl import OpenAIEmbedding
        model = OpenAIEmbedding(_make_config())
        assert model.getProvider() == "openai"

    @patch("cagr_processor.embedding.impl.openai_impl.OPENAI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.openai_impl._openai")
    def test_base_url_passed_to_client(self, mock_openai):
        mock_openai.OpenAI.return_value.embeddings = Mock()
        from cagr_processor.embedding.impl.openai_impl import OpenAIEmbedding
        OpenAIEmbedding(_make_config(base_url="http://proxy"))
        call_kwargs = mock_openai.OpenAI.call_args[1]
        assert call_kwargs["base_url"] == "http://proxy"
