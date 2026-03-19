"""EmbeddingFactory：按 provider 路由到具体嵌入模型实现"""

import logging
from typing import Dict, List, Optional, Type

from cagr_common.exceptions import EmbeddingConfigException
from cagr_processor.embedding.interfaces import EmbeddingModel
from cagr_processor.embedding.config import EmbeddingConfig

logger = logging.getLogger(__name__)


class EmbeddingFactory:
    """嵌入模型工厂

    通过 _registry 字典将 provider 字符串映射到具体实现类。
    支持运行时通过 register() 扩展新 provider。

    使用方式：
        config = EmbeddingConfig.from_env()
        model = EmbeddingFactory.create(config)
        vector = model.embed("some text")
    """

    _registry: Dict[str, Type[EmbeddingModel]] = {}

    @classmethod
    def _ensure_defaults_registered(cls) -> None:
        """延迟注册内置 provider，避免模块加载时因依赖缺失而报错"""
        if cls._registry:
            return
        try:
            from cagr_processor.embedding.impl.openai_impl import OpenAIEmbedding
            cls._registry["openai"] = OpenAIEmbedding
        except Exception:
            pass
        try:
            from cagr_processor.embedding.impl.gemini_impl import GeminiEmbedding
            cls._registry["gemini"] = GeminiEmbedding
        except Exception:
            pass
        try:
            from cagr_processor.embedding.impl.ollama_impl import OllamaEmbedding
            cls._registry["ollama"] = OllamaEmbedding
        except Exception:
            pass

    @classmethod
    def register(cls, provider: str, implementation: Type[EmbeddingModel]) -> None:
        """注册新的 provider 实现（支持运行时扩展或覆盖内置实现）"""
        cls._registry[provider.lower()] = implementation

    @classmethod
    def create(cls, config: EmbeddingConfig) -> EmbeddingModel:
        """根据 EmbeddingConfig 创建对应的嵌入模型实例"""
        cls._ensure_defaults_registered()
        if not config.provider:
            raise EmbeddingConfigException("provider must not be empty")
        if config.batch_size <= 0:
            raise EmbeddingConfigException("batch_size must be > 0")
        provider = config.provider.lower()
        impl_class = cls._registry.get(provider)
        if impl_class is None:
            raise EmbeddingConfigException(
                f"Unsupported embedding provider: '{provider}'. "
                f"Supported: {cls.get_supported_providers()}",
                provider=provider,
            )
        try:
            return impl_class(config)
        except Exception as e:
            raise EmbeddingConfigException(
                f"Failed to create embedding model for provider '{provider}': {e}",
                provider=provider,
            ) from e

    @classmethod
    def create_from_env(cls) -> EmbeddingModel:
        """从环境变量加载配置并创建嵌入模型实例"""
        config = EmbeddingConfig.from_env()
        return cls.create(config)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """返回当前已注册的所有 provider 名称列表"""
        cls._ensure_defaults_registered()
        return list(cls._registry.keys())

    @classmethod
    def is_supported(cls, provider: str) -> bool:
        """判断指定 provider 是否已注册"""
        cls._ensure_defaults_registered()
        return provider.lower() in cls._registry
