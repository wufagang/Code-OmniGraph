"""GeminiEmbedding 单元测试（全部使用 mock，不调用真实 API）"""
import pytest
from unittest.mock import Mock, patch

from cagr_common.exceptions import EmbeddingConfigException, EmbeddingConnectionException
from cagr_processor.embedding.config import EmbeddingConfig, GeminiEmbeddingConfig


def _make_config(**kwargs) -> EmbeddingConfig:
    defaults = {"api_key": "gm-test", "model": "models/text-embedding-004"}
    defaults.update(kwargs)
    return EmbeddingConfig(
        provider="gemini",
        gemini_config=GeminiEmbeddingConfig(**defaults),
    )


class TestGeminiEmbedding:
    @patch("cagr_processor.embedding.impl.gemini_impl.GEMINI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.gemini_impl._genai")
    def test_embed_returns_vector(self, mock_genai):
        mock_genai.embed_content.return_value = {"embedding": [0.1, 0.2, 0.3]}

        from cagr_processor.embedding.impl.gemini_impl import GeminiEmbedding
        model = GeminiEmbedding(_make_config())
        result = model.embed("hello")

        assert result == [0.1, 0.2, 0.3]
        mock_genai.embed_content.assert_called_once()

    @patch("cagr_processor.embedding.impl.gemini_impl.GEMINI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.gemini_impl._genai")
    def test_embed_passes_task_type(self, mock_genai):
        mock_genai.embed_content.return_value = {"embedding": [0.5]}

        from cagr_processor.embedding.impl.gemini_impl import GeminiEmbedding
        model = GeminiEmbedding(_make_config(task_type="RETRIEVAL_QUERY"))
        model.embed("query text")

        call_kwargs = mock_genai.embed_content.call_args[1]
        assert call_kwargs["task_type"] == "RETRIEVAL_QUERY"

    @patch("cagr_processor.embedding.impl.gemini_impl.GEMINI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.gemini_impl._genai")
    def test_connection_error_mapped(self, mock_genai):
        mock_genai.embed_content.side_effect = Exception("network unavailable")

        from cagr_processor.embedding.impl.gemini_impl import GeminiEmbedding
        model = GeminiEmbedding(_make_config())
        with pytest.raises(EmbeddingConnectionException):
            model.embed("text")

    @patch("cagr_processor.embedding.impl.gemini_impl.GEMINI_AVAILABLE", False)
    def test_raises_when_sdk_missing(self):
        from cagr_processor.embedding.impl.gemini_impl import GeminiEmbedding
        with pytest.raises(EmbeddingConfigException, match="google-generativeai"):
            GeminiEmbedding(_make_config())

    @patch("cagr_processor.embedding.impl.gemini_impl.GEMINI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.gemini_impl._genai")
    def test_detect_dimension(self, mock_genai):
        from cagr_processor.embedding.impl.gemini_impl import GeminiEmbedding
        model = GeminiEmbedding(_make_config())
        assert model.detectDimension() == 768

    @patch("cagr_processor.embedding.impl.gemini_impl.GEMINI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.gemini_impl._genai")
    def test_get_provider(self, mock_genai):
        from cagr_processor.embedding.impl.gemini_impl import GeminiEmbedding
        model = GeminiEmbedding(_make_config())
        assert model.getProvider() == "gemini"

    @patch("cagr_processor.embedding.impl.gemini_impl.GEMINI_AVAILABLE", True)
    @patch("cagr_processor.embedding.impl.gemini_impl._genai")
    def test_configure_called_with_api_key(self, mock_genai):
        from cagr_processor.embedding.impl.gemini_impl import GeminiEmbedding
        GeminiEmbedding(_make_config(api_key="my-key"))
        mock_genai.configure.assert_called_once_with(api_key="my-key")
