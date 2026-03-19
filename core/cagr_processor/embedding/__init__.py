"""
Code-OmniGraph 方法嵌入业务层模块

包含领域模型和业务服务：
- models.py：嵌入领域模型（MethodEmbedding、EmbeddingSearchResult、EmbeddingStats）
- embedding_service.py：EmbeddingService 业务层服务
"""

from .models import (
    EmbeddingTarget, CollectionName,
    MethodEmbedding, EmbeddingSearchResult, EmbeddingStats,
)
from .embedding_service import EmbeddingService

__all__ = [
    # 枚举
    "EmbeddingTarget", "CollectionName",
    # 数据模型
    "MethodEmbedding", "EmbeddingSearchResult", "EmbeddingStats",
    # 业务服务
    "EmbeddingService",
]
