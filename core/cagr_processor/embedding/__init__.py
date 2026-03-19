"""
Code-OmniGraph 方法嵌入业务层模块

包含两个子层：
1. 向量化层（interfaces / base / config / factory / impl）：纯文本 → 向量，与存储解耦
2. 业务服务层（embedding_service）：编排向量化 + 向量存储的完整流程
"""

# ---------- 业务模型 ----------
from .models import (
    EmbeddingTarget, CollectionName,
    MethodEmbedding, EmbeddingSearchResult, EmbeddingStats,
)

# ---------- 业务服务 ----------
from .embedding_service import EmbeddingService

# ---------- 向量化接口 & 配置 ----------
from .interfaces import EmbeddingModel
from .config import (
    EmbeddingConfig,
    OpenAIEmbeddingConfig,
    GeminiEmbeddingConfig,
    OllamaEmbeddingConfig,
)
from .factory import EmbeddingFactory

__all__ = [
    # 枚举
    "EmbeddingTarget", "CollectionName",
    # 业务数据模型
    "MethodEmbedding", "EmbeddingSearchResult", "EmbeddingStats",
    # 业务服务
    "EmbeddingService",
    # 向量化接口
    "EmbeddingModel",
    # 配置
    "EmbeddingConfig", "OpenAIEmbeddingConfig", "GeminiEmbeddingConfig", "OllamaEmbeddingConfig",
    # 工厂
    "EmbeddingFactory",
]
