"""业务层：方法嵌入服务（EmbeddingService）

职责：
- 接收领域对象（FunctionNode 等）
- 完成领域模型到向量数据的字段映射
- 将方法源码向量化后写入向量库
- 提供语义相似度搜索，返回领域对象
- 通过 VectorDatabase 接口与 DB 层解耦
"""

import logging
from typing import List, Optional, Dict, Any

from cagr_processor.embedding_dao.interfaces import VectorDatabase
from cagr_processor.embedding_dao.models import (
    VectorData, SearchParams, DistanceMetric,
)
from cagr_processor.embedding.models import (
    MethodEmbedding, EmbeddingSearchResult, EmbeddingStats, CollectionName,
)


class EmbeddingService:
    """方法嵌入业务服务层

    使用方式：
        db = VectorDBFactory.create(config)
        service = EmbeddingService(db)
        service.ensure_collection(vector_size=768)
        service.upsert_method(MethodEmbedding(...))
        results = service.search_similar_methods(query_vector=[...], limit=5)
    """

    def __init__(
        self,
        db: VectorDatabase,
        collection_name: str = CollectionName.FUNCTIONS,
    ):
        self._db = db
        self._collection_name = collection_name
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # 集合管理
    # ------------------------------------------------------------------

    def ensure_collection(
        self,
        vector_size: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
    ) -> bool:
        """若集合不存在则创建，已存在则跳过"""
        if self._db.has_collection(self._collection_name):
            return True
        return self._db.create_collection(
            collection_name=self._collection_name,
            vector_size=vector_size,
            distance_metric=distance_metric,
        )

    def drop_collection(self) -> bool:
        """删除集合（慎用）"""
        return self._db.drop_collection(self._collection_name)

    # ------------------------------------------------------------------
    # 写操作（领域模型 → VectorData 映射）
    # ------------------------------------------------------------------

    def upsert_method(self, embedding: MethodEmbedding) -> int:
        """写入或更新单个方法嵌入"""
        return self.upsert_methods([embedding])

    def upsert_methods(self, embeddings: List[MethodEmbedding]) -> int:
        """批量写入或更新方法嵌入"""
        data = [self._to_vector_data(e) for e in embeddings]
        return self._db.insert(self._collection_name, data)

    def delete_method(self, qualified_name: str) -> int:
        """按全限定名删除方法嵌入"""
        return self._db.delete(self._collection_name, ids=[qualified_name])

    # ------------------------------------------------------------------
    # 查询（SearchResult → EmbeddingSearchResult 映射）
    # ------------------------------------------------------------------

    def search_similar_methods(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[EmbeddingSearchResult]:
        """语义相似度搜索，返回最相关的方法列表"""
        params = SearchParams(
            collection_name=self._collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filter=filter,
        )
        raw_results = self._db.search(params)
        return [self._to_search_result(r) for r in raw_results]

    def get_stats(self) -> EmbeddingStats:
        """获取集合统计信息"""
        info = self._db.get_collection_info(self._collection_name)
        return EmbeddingStats(
            collection_name=self._collection_name,
            vector_count=info.vector_count or 0,
            vector_size=info.vector_size,
        )

    # ------------------------------------------------------------------
    # 内部转换
    # ------------------------------------------------------------------

    def _to_vector_data(self, embedding: MethodEmbedding) -> VectorData:
        """将 MethodEmbedding 转换为向量库 VectorData"""
        payload: Dict[str, Any] = {}
        for field_name in ("name", "signature", "body", "file_path", "class_name", "is_endpoint"):
            value = getattr(embedding, field_name, None)
            if value is not None:
                payload[field_name] = value
        payload.update(embedding.metadata)
        return VectorData(
            id=embedding.qualified_name,
            vector=embedding.vector,
            payload=payload if payload else None,
        )

    def _to_search_result(self, result: Any) -> EmbeddingSearchResult:
        """将向量库 SearchResult 转换为 EmbeddingSearchResult"""
        payload = result.payload or {}
        return EmbeddingSearchResult(
            qualified_name=str(result.id),
            score=result.score,
            name=payload.get("name"),
            signature=payload.get("signature"),
            body=payload.get("body"),
            file_path=payload.get("file_path"),
            class_name=payload.get("class_name"),
            is_endpoint=payload.get("is_endpoint", False),
        )
