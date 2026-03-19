import pytest
from unittest.mock import MagicMock, patch
from typing import List, Optional

from cagr_processor.embedding.interfaces import EmbeddingModel
from cagr_processor.embedding.config import EmbeddingConfig, OpenAIEmbeddingConfig


class ConcreteEmbedding(EmbeddingModel):
    """最小合规实现，用于验证接口契约"""
    def preprocessText(self, text: str) -> str:
        return text.strip()
    def preprocessTexts(self, texts: List[str]) -> List[str]:
        return [self.preprocessText(t) for t in texts]
    def detectDimension(self) -> int:
        return 768
    def embed(self, text: str) -> List[float]:
        return [0.1] * 768
    def embedBatch(self, texts, batch_size=None) -> List[List[float]]:
        return [self.embed(t) for t in texts]
    def getDimension(self) -> int:
        return self.detectDimension()
    def getProvider(self) -> str:
        return "mock"


class TestEmbeddingModelInterface:
    """验证 EmbeddingModel 接口的 7 个方法签名和基本契约"""

    def setup_method(self):
        self.model = ConcreteEmbedding()

    def test_preprocessText_returns_str(self):
        result = self.model.preprocessText("  hello  ")
        assert isinstance(result, str)
        assert result == "hello"

    def test_preprocessTexts_returns_list(self):
        result = self.model.preprocessTexts(["a", "b"])
        assert isinstance(result, list)
        assert len(result) == 2

    def test_detectDimension_returns_int(self):
        assert isinstance(self.model.detectDimension(), int)
        assert self.model.detectDimension() > 0

    def test_embed_returns_float_list(self):
        vector = self.model.embed("some code")
        assert isinstance(vector, list)
        assert len(vector) == 768
        assert all(isinstance(v, float) for v in vector)

    def test_embedBatch_returns_list_of_vectors(self):
        results = self.model.embedBatch(["a", "b", "c"])
        assert len(results) == 3
        for vec in results:
            assert isinstance(vec, list)

    def test_getDimension_returns_int(self):
        assert isinstance(self.model.getDimension(), int)
        assert self.model.getDimension() > 0

    def test_getProvider_returns_str(self):
        assert isinstance(self.model.getProvider(), str)
        assert len(self.model.getProvider()) > 0

    def test_cannot_instantiate_abc_directly(self):
        with pytest.raises(TypeError):
            EmbeddingModel()
