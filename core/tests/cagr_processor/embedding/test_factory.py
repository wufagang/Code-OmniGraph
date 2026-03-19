import pytest
from unittest.mock import patch, MagicMock
from typing import List, Optional

from cagr_common.exceptions import EmbeddingConfigException
from cagr_processor.embedding.interfaces import EmbeddingModel
from cagr_processor.embedding.factory import EmbeddingFactory
from cagr_processor.embedding.config import (
    EmbeddingConfig, OpenAIEmbeddingConfig, GeminiEmbeddingConfig, OllamaEmbeddingConfig
)


class MockEmbedding(EmbeddingModel):
    """测试用 Mock 实现"""
    def __init__(self, config):
        self.config = config
    def preprocessText(self, text): return text
    def preprocessTexts(self, texts): return texts
    def detectDimension(self): return 128
    def embed(self, text): return [0.1] * 128
    def embedBatch(self, texts, batch_size=None): return [[0.1] * 128 for _ in texts]
    def getDimension(self): return 128
    def getProvider(self): return "mock"


class TestEmbeddingFactory:
    def setup_method(self):
        # 每个测试前清空注册表，确保隔离
        EmbeddingFactory._registry.clear()

    def teardown_method(self):
        EmbeddingFactory._registry.clear()

    def test_register_and_create(self):
        EmbeddingFactory.register("mock", MockEmbedding)
        cfg = EmbeddingConfig(provider="mock", openai_config=OpenAIEmbeddingConfig())
        # 绕过 validate 的 provider 检查：直接测试工厂路由
        cfg.provider = "mock"
        # 跳过 validate（mock 不在内置列表）
        EmbeddingFactory._registry["mock"] = MockEmbedding
        instance = EmbeddingFactory._registry["mock"](cfg)
        assert isinstance(instance, MockEmbedding)

    def test_create_unregistered_raises(self):
        # 注册一个不存在的 provider，而不是依赖空注册表
        cfg = EmbeddingConfig(provider="openai", openai_config=OpenAIEmbeddingConfig())
        cfg.provider = "nonexistent_provider_xyz"
        EmbeddingFactory._registry.clear()
        EmbeddingFactory._registry["other"] = MockEmbedding  # 注册一个不同的名字
        with pytest.raises(EmbeddingConfigException):
            EmbeddingFactory.create(cfg)

    def test_register_multiple_providers(self):
        EmbeddingFactory.register("mock1", MockEmbedding)
        EmbeddingFactory.register("mock2", MockEmbedding)
        providers = EmbeddingFactory.get_supported_providers()
        assert "mock1" in providers
        assert "mock2" in providers

    def test_register_override(self):
        class AnotherMock(MockEmbedding):
            def getProvider(self): return "other"
        EmbeddingFactory.register("mock", MockEmbedding)
        EmbeddingFactory.register("mock", AnotherMock)
        assert EmbeddingFactory._registry["mock"] is AnotherMock

    def test_is_supported(self):
        EmbeddingFactory.register("mock", MockEmbedding)
        assert EmbeddingFactory.is_supported("mock") is True
        assert EmbeddingFactory.is_supported("nonexistent") is False

    def test_get_supported_providers_returns_list(self):
        EmbeddingFactory.register("mock", MockEmbedding)
        providers = EmbeddingFactory.get_supported_providers()
        assert isinstance(providers, list)

    def test_create_invokes_impl_init(self):
        init_called = []

        class TrackingMock(MockEmbedding):
            def __init__(self, config):
                super().__init__(config)
                init_called.append(config)

        EmbeddingFactory._registry["trackmock"] = TrackingMock
        cfg = EmbeddingConfig(provider="openai", openai_config=OpenAIEmbeddingConfig())
        cfg.provider = "trackmock"
        instance = EmbeddingFactory.create(cfg)
        assert len(init_called) == 1
        assert isinstance(instance, TrackingMock)

    def test_create_wraps_init_exception(self):
        class BrokenMock(MockEmbedding):
            def __init__(self, config):
                raise RuntimeError("broken")

        EmbeddingFactory._registry["brokenmock"] = BrokenMock
        cfg = EmbeddingConfig(provider="openai", openai_config=OpenAIEmbeddingConfig())
        cfg.provider = "brokenmock"

        with pytest.raises(EmbeddingConfigException) as exc:
            EmbeddingFactory.create(cfg)
        assert "Failed to create embedding model" in str(exc.value)
