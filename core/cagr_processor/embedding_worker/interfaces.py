from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union

from .models import (
    CollectionInfo, VectorData, SearchResult, SearchParams,
    HybridSearchParams, CollectionLimit, DistanceMetric, IndexType
)


class VectorDatabase(ABC):
    """向量数据库接口定义"""

    @abstractmethod
    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        index_type: Optional[IndexType] = None,
        **kwargs: Any
    ) -> bool:
        """
        创建集合

        Args:
            collection_name: 集合名称
            vector_size: 向量维度
            distance_metric: 距离度量方式
            index_type: 索引类型
            **kwargs: 其他参数

        Returns:
            是否创建成功

        Raises:
            CollectionAlreadyExistsException: 集合已存在
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def create_hybrid_collection(
        self,
        collection_name: str,
        dense_vector_size: int,
        sparse_vector_size: Optional[int] = None,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        **kwargs: Any
    ) -> bool:
        """
        创建混合向量集合（支持稠密和稀疏向量）

        Args:
            collection_name: 集合名称
            dense_vector_size: 稠密向量维度
            sparse_vector_size: 稀疏向量维度（可选）
            distance_metric: 距离度量方式
            **kwargs: 其他参数

        Returns:
            是否创建成功

        Raises:
            CollectionAlreadyExistsException: 集合已存在
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def drop_collection(self, collection_name: str) -> bool:
        """
        删除集合

        Args:
            collection_name: 集合名称

        Returns:
            是否删除成功

        Raises:
            CollectionNotFoundException: 集合不存在
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def has_collection(self, collection_name: str) -> bool:
        """
        检查集合是否存在

        Args:
            collection_name: 集合名称

        Returns:
            是否存在

        Raises:
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        """
        列出所有集合名称

        Returns:
            集合名称列表

        Raises:
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> CollectionInfo:
        """
        获取集合信息

        Args:
            collection_name: 集合名称

        Returns:
            集合信息

        Raises:
            CollectionNotFoundException: 集合不存在
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def insert(
        self,
        collection_name: str,
        data: List[VectorData],
        batch_size: Optional[int] = None
    ) -> int:
        """
        插入向量数据

        Args:
            collection_name: 集合名称
            data: 向量数据列表
            batch_size: 批量大小（可选）

        Returns:
            插入成功的数量

        Raises:
            CollectionNotFoundException: 集合不存在
            InsertException: 插入失败
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def insert_hybrid(
        self,
        collection_name: str,
        dense_data: List[VectorData],
        sparse_data: Optional[List[VectorData]] = None,
        batch_size: Optional[int] = None
    ) -> int:
        """
        插入混合向量数据（稠密和稀疏向量）

        Args:
            collection_name: 集合名称
            dense_data: 稠密向量数据列表
            sparse_data: 稀疏向量数据列表（可选）
            batch_size: 批量大小（可选）

        Returns:
            插入成功的数量

        Raises:
            CollectionNotFoundException: 集合不存在
            InsertException: 插入失败
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def search(self, params: SearchParams) -> List[SearchResult]:
        """
        向量搜索

        Args:
            params: 搜索参数

        Returns:
            搜索结果列表

        Raises:
            CollectionNotFoundException: 集合不存在
            SearchException: 搜索失败
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def hybrid_search(self, params: HybridSearchParams) -> List[SearchResult]:
        """
        混合向量搜索（稠密和稀疏向量）

        Args:
            params: 混合搜索参数

        Returns:
            搜索结果列表

        Raises:
            CollectionNotFoundException: 集合不存在
            SearchException: 搜索失败
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def delete(
        self,
        collection_name: str,
        ids: Optional[List[Union[str, int]]] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        删除向量数据

        Args:
            collection_name: 集合名称
            ids: 要删除的ID列表（可选）
            filter: 过滤条件（可选）

        Returns:
            删除的数量

        Raises:
            CollectionNotFoundException: 集合不存在
            DeleteException: 删除失败
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def query(
        self,
        collection_name: str,
        filter: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        with_vectors: bool = False
    ) -> List[VectorData]:
        """
        查询向量数据

        Args:
            collection_name: 集合名称
            filter: 过滤条件（可选）
            limit: 返回数量限制（可选）
            offset: 偏移量（可选）
            with_vectors: 是否包含向量数据

        Returns:
            向量数据列表

        Raises:
            CollectionNotFoundException: 集合不存在
            QueryException: 查询失败
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def check_collection_limit(self, collection_name: str) -> CollectionLimit:
        """
        检查集合限制信息

        Args:
            collection_name: 集合名称

        Returns:
            集合限制信息

        Raises:
            CollectionNotFoundException: 集合不存在
            ConnectionException: 连接失败
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭数据库连接"""
        pass