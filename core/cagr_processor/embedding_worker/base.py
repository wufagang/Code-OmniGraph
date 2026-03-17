import logging
from abc import ABC
from typing import List, Optional, Dict, Any, Union
import time
from functools import wraps

from .interfaces import VectorDatabase
from .models import (
    VectorData, CollectionInfo, SearchResult, SearchParams,
    HybridSearchParams, CollectionLimit, DistanceMetric, IndexType,
    InsertParams, DeleteParams, QueryParams
)
from .exceptions import (
    VectorDBException, ConnectionException, CollectionException,
    CollectionNotFoundException, CollectionAlreadyExistsException,
    InsertException, SearchException, DeleteException, QueryException
)


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(self, *args, **kwargs)
                except ConnectionException as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.warning(
                                f"{func.__name__} failed on attempt {attempt + 1}, "
                                f"retrying in {delay} seconds..."
                            )
                        time.sleep(delay)
                    else:
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
                except Exception as e:
                    # 非连接异常不重试
                    raise
            raise last_exception
        return wrapper
    return decorator


class BaseVectorDatabase(VectorDatabase, ABC):
    """向量数据库基础抽象类"""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._connection = None
        self._collection_cache = {}  # 集合信息缓存

    def _validate_connection(self):
        """验证连接状态"""
        if not self._connection:
            raise ConnectionException("Database connection is not established")

    def _validate_collection_name(self, collection_name: str):
        """验证集合名称"""
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("Collection name must be a non-empty string")
        if len(collection_name) > 255:
            raise ValueError("Collection name must not exceed 255 characters")

    def _validate_vector_data(self, data: List[VectorData]):
        """验证向量数据"""
        if not data:
            raise ValueError("Vector data list cannot be empty")

        # 检查向量维度一致性
        if len(data) > 1:
            first_vector_size = len(data[0].vector)
            for i, item in enumerate(data[1:], 1):
                if len(item.vector) != first_vector_size:
                    raise ValueError(
                        f"Inconsistent vector dimensions: item 0 has {first_vector_size}, "
                        f"item {i} has {len(item.vector)}"
                    )

    def _batch_operation(self, items: List[Any], batch_size: int, operation_func):
        """批量操作辅助方法"""
        total_success = 0

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            try:
                success_count = operation_func(batch)
                total_success += success_count
            except Exception as e:
                self.logger.error(f"Batch operation failed at offset {i}: {e}")
                raise

        return total_success

    def _log_operation(self, operation: str, collection_name: str, **kwargs):
        """记录操作日志"""
        if self.config.enable_logging:
            self.logger.info(
                f"{operation} on collection '{collection_name}' - "
                f"params: {kwargs}"
            )

    def _update_collection_cache(self, collection_name: str, info: CollectionInfo):
        """更新集合缓存"""
        self._collection_cache[collection_name] = info

    def _get_from_cache(self, collection_name: str) -> Optional[CollectionInfo]:
        """从缓存获取集合信息"""
        return self._collection_cache.get(collection_name)

    def _clear_collection_cache(self, collection_name: str):
        """清除集合缓存"""
        self._collection_cache.pop(collection_name, None)

    # 基础实现，子类可以重写
    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        index_type: Optional[IndexType] = None,
        **kwargs: Any
    ) -> bool:
        """创建集合的基础实现"""
        self._validate_collection_name(collection_name)
        self._log_operation("create_collection", collection_name,
                          vector_size=vector_size, distance_metric=distance_metric)
        return self._create_collection_impl(
            collection_name, vector_size, distance_metric, index_type, **kwargs
        )

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_hybrid_collection(
        self,
        collection_name: str,
        dense_vector_size: int,
        sparse_vector_size: Optional[int] = None,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        **kwargs: Any
    ) -> bool:
        """创建混合向量集合的基础实现"""
        self._validate_collection_name(collection_name)
        self._log_operation("create_hybrid_collection", collection_name,
                          dense_vector_size=dense_vector_size,
                          sparse_vector_size=sparse_vector_size,
                          distance_metric=distance_metric)
        return self._create_hybrid_collection_impl(
            collection_name, dense_vector_size, sparse_vector_size, distance_metric, **kwargs
        )

    @retry_on_failure(max_attempts=3, delay=1.0)
    def insert(
        self,
        collection_name: str,
        data: List[VectorData],
        batch_size: Optional[int] = None
    ) -> int:
        """插入数据的基础实现"""
        self._validate_collection_name(collection_name)
        self._validate_vector_data(data)

        if not self.has_collection(collection_name):
            raise CollectionNotFoundException(f"Collection '{collection_name}' not found", collection_name)

        # 使用配置的批量大小或默认值
        if batch_size is None:
            batch_size = getattr(self.config, 'default_batch_size', 100)

        # 确保batch_size是整数
        if isinstance(batch_size, int):
            actual_batch_size = batch_size
        else:
            actual_batch_size = 100

        self._log_operation("insert", collection_name, data_count=len(data), batch_size=actual_batch_size)

        if len(data) <= actual_batch_size:
            return self._insert_impl(collection_name, data)
        else:
            return self._batch_operation(data, actual_batch_size,
                                       lambda batch: self._insert_impl(collection_name, batch))

    @retry_on_failure(max_attempts=3, delay=1.0)
    def search(self, params: SearchParams) -> List[SearchResult]:
        """搜索的基础实现"""
        self._validate_collection_name(params.collection_name)
        self._log_operation("search", params.collection_name, limit=params.limit)

        if not self.has_collection(params.collection_name):
            raise CollectionNotFoundException(f"Collection '{params.collection_name}' not found",
                                            params.collection_name)

        return self._search_impl(params)

    @retry_on_failure(max_attempts=3, delay=1.0)
    def delete(
        self,
        collection_name: str,
        ids: Optional[List[Union[str, int]]] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """删除的基础实现"""
        self._validate_collection_name(collection_name)

        if not ids and not filter:
            raise ValueError("Either ids or filter must be provided")

        if not self.has_collection(collection_name):
            raise CollectionNotFoundException(f"Collection '{collection_name}' not found", collection_name)

        self._log_operation("delete", collection_name, ids_count=len(ids) if ids else 0)
        return self._delete_impl(collection_name, ids, filter)

    # 子类必须实现的抽象方法
    def _create_collection_impl(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: DistanceMetric,
        index_type: Optional[IndexType],
        **kwargs: Any
    ) -> bool:
        """子类实现具体的集合创建逻辑"""
        raise NotImplementedError

    def _create_hybrid_collection_impl(
        self,
        collection_name: str,
        dense_vector_size: int,
        sparse_vector_size: Optional[int],
        distance_metric: DistanceMetric,
        **kwargs: Any
    ) -> bool:
        """子类实现具体的混合集合创建逻辑"""
        raise NotImplementedError

    def _insert_impl(self, collection_name: str, data: List[VectorData]) -> int:
        """子类实现具体的插入逻辑"""
        raise NotImplementedError

    def _search_impl(self, params: SearchParams) -> List[SearchResult]:
        """子类实现具体的搜索逻辑"""
        raise NotImplementedError

    def _delete_impl(
        self,
        collection_name: str,
        ids: Optional[List[Union[str, int]]],
        filter: Optional[Dict[str, Any]]
    ) -> int:
        """子类实现具体的删除逻辑"""
        raise NotImplementedError