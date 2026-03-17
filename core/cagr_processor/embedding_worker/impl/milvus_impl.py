import logging
from typing import List, Optional, Dict, Any, Union

try:
    from pymilvus import (
        connections, Collection, FieldSchema, CollectionSchema,
        DataType, utility, SearchResult as MilvusSearchResult
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

from ..base import BaseVectorDatabase
from ..models import (
    VectorData, CollectionInfo, SearchResult, SearchParams,
    HybridSearchParams, CollectionLimit, DistanceMetric, IndexType
)
from ..exceptions import (
    ConnectionException, CollectionNotFoundException,
    CollectionAlreadyExistsException, InsertException,
    SearchException, DeleteException, QueryException,
    ConfigException
)


class MilvusDistanceMapper:
    """Milvus距离度量映射器"""
    @staticmethod
    def to_milvus(distance: DistanceMetric) -> str:
        mapping = {
            DistanceMetric.COSINE: "COSINE",
            DistanceMetric.EUCLIDEAN: "L2",
            DistanceMetric.DOT_PRODUCT: "IP",
            DistanceMetric.HAMMING: "HAMMING",
        }
        return mapping.get(distance, "COSINE")


class MilvusIndexMapper:
    """Milvus索引类型映射器"""
    @staticmethod
    def get_index_params(index_type: Optional[IndexType], distance: DistanceMetric) -> Dict[str, Any]:
        """获取索引参数"""
        if index_type == IndexType.HNSW:
            return {
                "index_type": "HNSW",
                "metric_type": MilvusDistanceMapper.to_milvus(distance),
                "params": {"M": 16, "efConstruction": 200}
            }
        elif index_type == IndexType.IVF_FLAT:
            return {
                "index_type": "IVF_FLAT",
                "metric_type": MilvusDistanceMapper.to_milvus(distance),
                "params": {"nlist": 128}
            }
        else:
            # 默认使用HNSW
            return {
                "index_type": "HNSW",
                "metric_type": MilvusDistanceMapper.to_milvus(distance),
                "params": {"M": 16, "efConstruction": 200}
            }


class MilvusDatabase(BaseVectorDatabase):
    """Milvus向量数据库实现"""

    def __init__(self, config):
        super().__init__(config)
        self._connection_alias = None
        if MILVUS_AVAILABLE:
            self._connect()
        else:
            self.logger.warning("Milvus client library is not installed. Using mock mode.")
            self._connection_alias = None

    def _connect(self):
        """建立连接"""
        if not MILVUS_AVAILABLE:
            raise ConfigException(
                "Milvus client library (pymilvus) is not installed. "
                "Please install it with: pip install pymilvus"
            )
        try:
            milvus_config = self.config.milvus_config

            # 生成唯一的连接别名
            self._connection_alias = f"milvus_{id(self)}"

            # 连接参数
            connect_params = {
                "alias": self._connection_alias,
                "secure": milvus_config.secure,
                "db_name": milvus_config.db_name,
            }

            if milvus_config.uri:
                connect_params["uri"] = milvus_config.uri
                if milvus_config.user and milvus_config.password:
                    connect_params["user"] = milvus_config.user
                    connect_params["password"] = milvus_config.password
                if milvus_config.token:
                    connect_params["token"] = milvus_config.token
            else:
                connect_params["host"] = milvus_config.host
                connect_params["port"] = milvus_config.port
                if milvus_config.user and milvus_config.password:
                    connect_params["user"] = milvus_config.user
                    connect_params["password"] = milvus_config.password

            if milvus_config.client_timeout:
                connect_params["timeout"] = milvus_config.client_timeout

            connections.connect(**connect_params)
            self.logger.info("Successfully connected to Milvus")

        except Exception as e:
            self.logger.error(f"Failed to connect to Milvus: {e}")
            raise ConnectionException(f"Failed to connect to Milvus: {e}")

    def close(self) -> None:
        """关闭连接"""
        if self._connection_alias:
            try:
                connections.disconnect(self._connection_alias)
                self.logger.info("Milvus connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing Milvus connection: {e}")
            finally:
                self._connection_alias = None

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
            if utility.has_collection(collection_name, using=self._connection_alias):
                raise CollectionAlreadyExistsException(
                    f"Collection '{collection_name}' already exists", collection_name
                )

            # 定义字段
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=512, is_primary=True),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=vector_size),
            ]

            # 添加payload字段（可选）
            if kwargs.get("enable_payload", True):
                fields.append(FieldSchema(name="payload", dtype=DataType.JSON))

            # 创建schema
            schema = CollectionSchema(
                fields=fields,
                description=kwargs.get("description", ""),
                enable_dynamic_field=kwargs.get("enable_dynamic_field", True)
            )

            # 创建集合
            collection = Collection(
                name=collection_name,
                schema=schema,
                using=self._connection_alias
            )

            # 创建索引
            index_params = MilvusIndexMapper.get_index_params(index_type, distance_metric)
            collection.create_index("vector", index_params)

            # 加载集合
            collection.load()

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

        except CollectionAlreadyExistsException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create collection '{collection_name}': {e}")
            raise InsertException(f"Failed to create collection: {e}")

    def drop_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            if not utility.has_collection(collection_name, using=self._connection_alias):
                raise CollectionNotFoundException(
                    f"Collection '{collection_name}' not found", collection_name
                )

            # 释放集合
            collection = Collection(collection_name, using=self._connection_alias)
            collection.release()

            # 删除集合
            utility.drop_collection(collection_name, using=self._connection_alias)
            self._clear_collection_cache(collection_name)

            self.logger.info(f"Collection '{collection_name}' dropped successfully")
            return True

        except CollectionNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to drop collection '{collection_name}': {e}")
            raise DeleteException(f"Failed to drop collection: {e}")

    def has_collection(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        try:
            return utility.has_collection(collection_name, using=self._connection_alias)
        except Exception as e:
            self.logger.error(f"Failed to check collection '{collection_name}': {e}")
            raise ConnectionException(f"Failed to check collection: {e}")

    def list_collections(self) -> List[str]:
        """列出所有集合"""
        try:
            return utility.list_collections(using=self._connection_alias)
        except Exception as e:
            self.logger.error(f"Failed to list collections: {e}")
            raise ConnectionException(f"Failed to list collections: {e}")

    def get_collection_info(self, collection_name: str) -> CollectionInfo:
        """获取集合信息"""
        try:
            # 先检查缓存
            cached_info = self._get_from_cache(collection_name)
            if cached_info:
                return cached_info

            if not utility.has_collection(collection_name, using=self._connection_alias):
                raise CollectionNotFoundException(
                    f"Collection '{collection_name}' not found", collection_name
                )

            collection = Collection(collection_name, using=self._connection_alias)

            # 获取统计信息
            collection.flush()
            stats = collection.num_entities

            # 获取schema信息
            schema = collection.schema
            vector_size = 0

            for field in schema.fields:
                if field.dtype == DataType.FLOAT_VECTOR:
                    vector_size = field.params.get("dim", 0)
                    break

            info = CollectionInfo(
                name=collection_name,
                vector_size=vector_size,
                distance_metric=DistanceMetric.COSINE,  # 默认值
                vector_count=stats
            )

            self._update_collection_cache(collection_name, info)
            return info

        except CollectionNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get collection info '{collection_name}': {e}")
            raise QueryException(f"Failed to get collection info: {e}")

    def _insert_impl(self, collection_name: str, data: List[VectorData]) -> int:
        """插入数据实现"""
        try:
            collection = Collection(collection_name, using=self._connection_alias)

            # 准备数据
            ids = [str(item.id) for item in data]
            vectors = [item.vector for item in data]
            payloads = [item.payload or {} for item in data]

            # 插入数据
            entities = [
                ids,
                vectors,
                payloads
            ]

            result = collection.insert(entities)
            collection.flush()

            return len(result.primary_keys)

        except Exception as e:
            self.logger.error(f"Failed to insert data into '{collection_name}': {e}")
            raise InsertException(f"Failed to insert data: {e}")

    def _search_impl(self, params: SearchParams) -> List[SearchResult]:
        """搜索实现"""
        try:
            collection = Collection(params.collection_name, using=self._connection_alias)

            # 构建搜索参数
            search_params = self.config.milvus_config.search_params or {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }

            # 执行搜索
            results = collection.search(
                data=[params.query_vector],
                anns_field="vector",
                param=search_params,
                limit=params.limit,
                offset=params.offset or 0,
                output_fields=["payload"] if params.with_vectors else ["payload"]
            )

            # 转换结果
            search_results = []
            for hits in results:
                for hit in hits:
                    result = SearchResult(
                        id=hit.id,
                        score=hit.score,
                        payload=hit.entity.get("payload") if hasattr(hit, 'entity') else None
                    )
                    search_results.append(result)

            return search_results

        except Exception as e:
            self.logger.error(f"Failed to search in '{params.collection_name}': {e}")
            raise SearchException(f"Failed to search: {e}")

    def _delete_impl(
        self,
        collection_name: str,
        ids: Optional[List[Union[str, int]]],
        filter: Optional[Dict[str, Any]]
    ) -> int:
        """删除实现"""
        try:
            collection = Collection(collection_name, using=self._connection_alias)

            expr = None
            if ids:
                # 构建ID表达式
                id_list = ["'{}'".format(str(id)) for id in ids]
                expr = "id in [{}]".format(','.join(id_list))
            elif filter:
                # 转换过滤条件为Milvus表达式
                expr = self._convert_filter_to_expr(filter)

            result = collection.delete(expr)
            collection.flush()

            return result.delete_count

        except Exception as e:
            self.logger.error(f"Failed to delete from '{collection_name}': {e}")
            raise DeleteException(f"Failed to delete: {e}")

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

            collection = Collection(collection_name, using=self._connection_alias)

            # 构建查询表达式
            expr = None
            if filter:
                expr = self._convert_filter_to_expr(filter)

            # 设置输出字段
            output_fields = ["id", "payload"]
            if with_vectors:
                output_fields.append("vector")

            # 执行查询
            results = collection.query(
                expr=expr,
                output_fields=output_fields,
                limit=limit,
                offset=offset
            )

            # 转换结果
            vector_data_list = []
            for result in results:
                vector_data = VectorData(
                    id=result["id"],
                    vector=result.get("vector", []) if with_vectors else [],
                    payload=result.get("payload")
                )
                vector_data_list.append(vector_data)

            return vector_data_list

        except CollectionNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to query '{collection_name}': {e}")
            raise QueryException(f"Failed to query: {e}")

    def insert_hybrid(
        self,
        collection_name: str,
        dense_data: List[VectorData],
        sparse_data: Optional[List[VectorData]] = None,
        batch_size: Optional[int] = None
    ) -> int:
        """插入混合向量数据"""
        # 对于不支持混合向量的版本，只处理稠密向量
        return self.insert(collection_name, dense_data, batch_size)

    def hybrid_search(self, params: HybridSearchParams) -> List[SearchResult]:
        """混合向量搜索"""
        # 对于不支持混合搜索的版本，只使用稠密向量搜索
        search_params = SearchParams(
            collection_name=params.collection_name,
            query_vector=params.dense_vector,
            limit=params.limit,
            score_threshold=params.score_threshold,
            filter=params.filter,
            with_vectors=False
        )
        return self.search(search_params)

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
            raise QueryException(f"Failed to check collection limit: {e}")

    def _convert_filter_to_expr(self, filter_dict: Dict[str, Any]) -> str:
        """转换过滤条件为Milvus表达式"""
        conditions = []

        for key, value in filter_dict.items():
            if isinstance(value, str):
                conditions.append('{} == \"{}\"'.format(key, value))
            else:
                conditions.append('{} == {}'.format(key, value))

        return " and ".join(conditions) if conditions else None