import logging
from typing import List, Optional, Dict, Any, Union

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        PointStruct, VectorParams, Distance,
        SearchRequest, Filter, FieldCondition, MatchValue,
        UpdateStatus, SparseVector, SparseVectorParams
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from ..base import BaseVectorDatabase
from ..models import (
    VectorData, CollectionInfo, SearchResult, SearchParams,
    HybridSearchParams, CollectionLimit, DistanceMetric, IndexType
)
from cagr_common.exceptions import (
    VectorConnectionException, VectorCollectionNotFoundException,
    VectorCollectionAlreadyExistsException, VectorInsertException,
    VectorSearchException, VectorDeleteException, VectorQueryException
)


class QdrantDistanceMapper:
    """Qdrant距离度量映射器"""
    @staticmethod
    def to_qdrant(distance: DistanceMetric):
        """将距离度量转换为Qdrant格式"""
        if not QDRANT_AVAILABLE:
            return "COSINE"  # 默认值

        from qdrant_client.models import Distance
        mapping = {
            DistanceMetric.COSINE: Distance.COSINE,
            DistanceMetric.EUCLIDEAN: Distance.EUCLID,
            DistanceMetric.DOT_PRODUCT: Distance.DOT,
        }
        return mapping.get(distance, Distance.COSINE)


class QdrantDatabase(BaseVectorDatabase):
    """Qdrant向量数据库实现"""

    def __init__(self, config):
        super().__init__(config)
        self._client: Optional[QdrantClient] = None
        if QDRANT_AVAILABLE:
            self._connect()
        else:
            self.logger.warning("Qdrant client library is not installed. Using mock mode.")
            self._client = None

    def _connect(self):
        """建立连接"""
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "Qdrant client library is not installed. "
                "Please install it with: pip install qdrant-client"
            )
        try:
            qdrant_config = self.config.qdrant_config
            if qdrant_config.url:
                self._client = QdrantClient(
                    url=qdrant_config.url,
                    api_key=qdrant_config.api_key,
                    prefer_grpc=qdrant_config.prefer_grpc,
                    timeout=qdrant_config.timeout,
                    https=qdrant_config.https,
                    prefix=qdrant_config.prefix,
                )
            else:
                self._client = QdrantClient(
                    host=qdrant_config.host,
                    port=qdrant_config.port,
                    api_key=qdrant_config.api_key,
                    prefer_grpc=qdrant_config.prefer_grpc,
                    timeout=qdrant_config.timeout,
                    https=qdrant_config.https,
                    prefix=qdrant_config.prefix,
                )

            # 测试连接
            self._client.get_collections()
            self.logger.info("Successfully connected to Qdrant")

        except Exception as e:
            self.logger.error(f"Failed to connect to Qdrant: {e}")
            raise VectorConnectionException(f"Failed to connect to Qdrant: {e}")

    def close(self) -> None:
        """关闭连接"""
        if self._client:
            # Qdrant客户端没有显式的close方法
            self._client = None
            self.logger.info("Qdrant connection closed")

    def _create_collection_impl(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: DistanceMetric,
        index_type: Optional[IndexType],
        **kwargs: Any
    ) -> bool:
        """创建集合实现"""
        try:
            if self._client.collection_exists(collection_name):
                raise VectorCollectionAlreadyExistsException(
                    f"Collection '{collection_name}' already exists", collection_name
                )

            distance = QdrantDistanceMapper.to_qdrant(distance_metric)
            if QDRANT_AVAILABLE:
                from qdrant_client.models import VectorParams
                self._client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance),
                    **kwargs
                )
            else:
                raise ImportError("qdrant-client library is not installed")

            # 更新缓存
            info = CollectionInfo(
                name=collection_name,
                vector_size=vector_size,
                distance_metric=distance_metric,
                index_type=index_type
            )
            self._update_collection_cache(collection_name, info)

            self.logger.info(f"Collection '{collection_name}' created successfully")
            return True

        except VectorCollectionAlreadyExistsException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create collection '{collection_name}': {e}")
            raise VectorInsertException(f"Failed to create collection: {e}")

    def _create_hybrid_collection_impl(
        self,
        collection_name: str,
        dense_vector_size: int,
        sparse_vector_size: Optional[int],
        distance_metric: DistanceMetric,
        **kwargs: Any
    ) -> bool:
        """创建混合向量集合实现"""
        try:
            if self._client.collection_exists(collection_name):
                raise VectorCollectionAlreadyExistsException(
                    f"Collection '{collection_name}' already exists", collection_name
                )

            distance = QdrantDistanceMapper.to_qdrant(distance_metric)

            # 创建支持多种向量类型的集合
            vectors_config = {
                "dense": VectorParams(size=dense_vector_size, distance=distance),
            }

            # 如果指定了稀疏向量维度，添加稀疏向量配置
            if sparse_vector_size:
                vectors_config["sparse"] = SparseVectorParams()

            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                **kwargs
            )

            self.logger.info(f"Hybrid collection '{collection_name}' created successfully")
            return True

        except VectorCollectionAlreadyExistsException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create hybrid collection '{collection_name}': {e}")
            raise VectorInsertException(f"Failed to create hybrid collection: {e}")

    def drop_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            if not self._client.collection_exists(collection_name):
                raise CollectionNotFoundException(
                    f"Collection '{collection_name}' not found", collection_name
                )

            self._client.delete_collection(collection_name)
            self._clear_collection_cache(collection_name)
            self.logger.info(f"Collection '{collection_name}' dropped successfully")
            return True

        except CollectionNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to drop collection '{collection_name}': {e}")
            raise VectorDeleteException(f"Failed to drop collection: {e}")

    def has_collection(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        try:
            return self._client.collection_exists(collection_name)
        except Exception as e:
            self.logger.error(f"Failed to check collection '{collection_name}': {e}")
            raise VectorConnectionException(f"Failed to check collection: {e}")

    def list_collections(self) -> List[str]:
        """列出所有集合"""
        try:
            collections = self._client.get_collections()
            return [col.name for col in collections.collections]
        except Exception as e:
            self.logger.error(f"Failed to list collections: {e}")
            raise VectorConnectionException(f"Failed to list collections: {e}")

    def get_collection_info(self, collection_name: str) -> CollectionInfo:
        """获取集合信息"""
        try:
            # 先检查缓存
            cached_info = self._get_from_cache(collection_name)
            if cached_info:
                return cached_info

            if not self._client.collection_exists(collection_name):
                raise CollectionNotFoundException(
                    f"Collection '{collection_name}' not found", collection_name
                )

            info = self._client.get_collection(collection_name)

            # 解析配置信息
            vector_config = info.config.params.vectors
            if QDRANT_AVAILABLE:
                from qdrant_client.models import Distance
                if isinstance(vector_config, dict):
                    # 多向量配置
                    vector_size = vector_config.get('dense', {}).get('size', 0)
                    distance_metric = DistanceMetric.COSINE  # 默认
                else:
                    # 单向量配置
                    vector_size = vector_config.size
                    distance = vector_config.distance
                    if distance == Distance.COSINE:
                        distance_metric = DistanceMetric.COSINE
                    elif distance == Distance.EUCLIDEAN:
                        distance_metric = DistanceMetric.EUCLIDEAN
                    else:
                        distance_metric = DistanceMetric.DOT_PRODUCT
            else:
                vector_size = 0
                distance_metric = DistanceMetric.COSINE

            collection_info = CollectionInfo(
                name=collection_name,
                vector_size=vector_size,
                distance_metric=distance_metric,
                vector_count=info.points_count
            )

            self._update_collection_cache(collection_name, collection_info)
            return collection_info

        except CollectionNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get collection info '{collection_name}': {e}")
            raise VectorQueryException(f"Failed to get collection info: {e}")

    def _insert_impl(self, collection_name: str, data: List[VectorData]) -> int:
        """插入数据实现"""
        try:
            if not QDRANT_AVAILABLE:
                raise ImportError("qdrant-client library is not installed")

            from qdrant_client.models import PointStruct, UpdateStatus

            points = []
            for item in data:
                point = PointStruct(
                    id=item.id,
                    vector=item.vector,
                    payload=item.payload or {}
                )
                points.append(point)

            result = self._client.upsert(
                collection_name=collection_name,
                points=points
            )

            if result.status == UpdateStatus.COMPLETED:
                return len(data)
            else:
                raise VectorInsertException(f"Insert operation status: {result.status}")

        except Exception as e:
            self.logger.error(f"Failed to insert data into '{collection_name}': {e}")
            raise VectorInsertException(f"Failed to insert data: {e}")

    def insert_hybrid(
        self,
        collection_name: str,
        dense_data: List[VectorData],
        sparse_data: Optional[List[VectorData]] = None,
        batch_size: Optional[int] = None
    ) -> int:
        """插入混合向量数据"""
        try:
            if not self.has_collection(collection_name):
                raise CollectionNotFoundException(
                    f"Collection '{collection_name}' not found", collection_name
                )

            # 构建点数据
            if not QDRANT_AVAILABLE:
                raise ImportError("qdrant-client library is not installed")

            from qdrant_client.models import PointStruct, UpdateStatus, SparseVector

            points = []
            for i, dense_item in enumerate(dense_data):
                vectors = {"dense": dense_item.vector}

                # 如果有对应的稀疏向量，添加进去
                if sparse_data and i < len(sparse_data):
                    sparse_item = sparse_data[i]
                    # 将稀疏向量转换为SparseVector格式
                    indices = []
                    values = []
                    for idx, val in enumerate(sparse_item.vector):
                        if val != 0:
                            indices.append(idx)
                            values.append(float(val))
                    vectors["sparse"] = SparseVector(indices=indices, values=values)

                point = PointStruct(
                    id=dense_item.id,
                    vector=vectors,
                    payload=dense_item.payload or {}
                )
                points.append(point)

            result = self._client.upsert(
                collection_name=collection_name,
                points=points
            )

            if result.status == UpdateStatus.COMPLETED:
                return len(dense_data)
            else:
                raise VectorInsertException(f"Hybrid insert operation status: {result.status}")

        except CollectionNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to insert hybrid data into '{collection_name}': {e}")
            raise VectorInsertException(f"Failed to insert hybrid data: {e}")

    def _search_impl(self, params: SearchParams) -> List[SearchResult]:
        """搜索实现"""
        try:
            search_result = self._client.search(
                collection_name=params.collection_name,
                query_vector=params.query_vector,
                limit=params.limit,
                score_threshold=params.score_threshold,
                with_payload=True,
                with_vectors=params.with_vectors,
                offset=params.offset
            )

            results = []
            for point in search_result:
                result = SearchResult(
                    id=point.id,
                    score=point.score,
                    payload=point.payload,
                    vector=point.vector if params.with_vectors else None
                )
                results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"Failed to search in '{params.collection_name}': {e}")
            raise VectorSearchException(f"Failed to search: {e}")

    def hybrid_search(self, params: HybridSearchParams) -> List[SearchResult]:
        """混合向量搜索"""
        try:
            if not self.has_collection(params.collection_name):
                raise CollectionNotFoundException(
                    f"Collection '{params.collection_name}' not found", params.collection_name
                )

            # 构建查询向量
            query_vector = {
                "dense": params.dense_vector,
            }

            if params.sparse_vector and QDRANT_AVAILABLE:
                from qdrant_client.models import SparseVector
                # 转换稀疏向量
                indices = []
                values = []
                for idx, val in params.sparse_vector.items():
                    indices.append(int(idx))
                    values.append(float(val))
                query_vector["sparse"] = SparseVector(indices=indices, values=values)

            search_result = self._client.search(
                collection_name=params.collection_name,
                query_vector=query_vector,
                limit=params.limit,
                score_threshold=params.score_threshold,
                with_payload=True,
                with_vectors=False
            )

            results = []
            for point in search_result:
                result = SearchResult(
                    id=point.id,
                    score=point.score,
                    payload=point.payload
                )
                results.append(result)

            return results

        except CollectionNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to hybrid search in '{params.collection_name}': {e}")
            raise VectorSearchException(f"Failed to hybrid search: {e}")

    def _delete_impl(
        self,
        collection_name: str,
        ids: Optional[List[Union[str, int]]],
        filter: Optional[Dict[str, Any]]
    ) -> int:
        """删除实现"""
        try:
            if not QDRANT_AVAILABLE:
                raise ImportError("qdrant-client library is not installed")

            from qdrant_client.models import UpdateStatus

            points_selector = None

            if ids:
                points_selector = ids
            elif filter:
                # 转换过滤条件
                qdrant_filter = self._convert_filter(filter)
                points_selector = qdrant_filter

            result = self._client.delete(
                collection_name=collection_name,
                points_selector=points_selector
            )

            if result.status == UpdateStatus.COMPLETED:
                # Qdrant不返回删除数量，我们假设全部删除成功
                return len(ids) if ids else -1
            else:
                raise VectorDeleteException(f"Delete operation status: {result.status}")

        except Exception as e:
            self.logger.error(f"Failed to delete from '{collection_name}': {e}")
            raise VectorDeleteException(f"Failed to delete: {e}")

    def query(
        self,
        collection_name: str,
        filter: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        with_vectors: bool = False
    ) -> List[VectorData]:
        """查询向量数据"""
        try:
            if not self.has_collection(collection_name):
                raise CollectionNotFoundException(
                    f"Collection '{collection_name}' not found", collection_name
                )

            if not QDRANT_AVAILABLE:
                raise ImportError("qdrant-client library is not installed")

            qdrant_filter = None
            if filter:
                qdrant_filter = self._convert_filter(filter)

            result = self._client.scroll(
                collection_name=collection_name,
                scroll_filter=qdrant_filter,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=with_vectors
            )

            points, _ = result

            vector_data_list = []
            for point in points:
                vector_data = VectorData(
                    id=point.id,
                    vector=point.vector if with_vectors else [],
                    payload=point.payload
                )
                vector_data_list.append(vector_data)

            return vector_data_list

        except CollectionNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to query '{collection_name}': {e}")
            raise VectorQueryException(f"Failed to query: {e}")

    def check_collection_limit(self, collection_name: str) -> CollectionLimit:
        """检查集合限制"""
        try:
            info = self.get_collection_info(collection_name)
            return CollectionLimit(
                current_vectors=info.vector_count,
                current_collections=len(self.list_collections())
            )
        except Exception as e:
            self.logger.error(f"Failed to check collection limit for '{collection_name}': {e}")
            raise VectorQueryException(f"Failed to check collection limit: {e}")

    def _convert_filter(self, filter_dict: Dict[str, Any]):
        """转换过滤条件"""
        if not QDRANT_AVAILABLE:
            return None

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        must_conditions = []

        for key, value in filter_dict.items():
            condition = FieldCondition(
                key=key,
                match=MatchValue(value=value)
            )
            must_conditions.append(condition)

        return Filter(must=must_conditions) if must_conditions else None