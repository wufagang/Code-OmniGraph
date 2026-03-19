import pytest
from dataclasses import dataclass

from cagr_processor.embedding_dao.models import (
    VectorData, CollectionInfo, SearchResult, SearchParams,
    HybridSearchParams, CollectionLimit, DistanceMetric, IndexType,
    InsertParams, DeleteParams, QueryParams
)


class TestModels:
    """测试数据模型"""

    def test_vector_data(self):
        """测试VectorData模型"""
        # 基本测试
        data = VectorData(
            id="test_id",
            vector=[0.1, 0.2, 0.3],
            payload={"key": "value"}
        )
        assert data.id == "test_id"
        assert data.vector == [0.1, 0.2, 0.3]
        assert data.payload == {"key": "value"}

        # 测试可选payload
        data_no_payload = VectorData(id="1", vector=[1.0, 2.0])
        assert data_no_payload.payload is None

        # 测试数字ID
        data_numeric = VectorData(id=123, vector=[0.1, 0.2])
        assert data_numeric.id == 123

    def test_collection_info(self):
        """测试CollectionInfo模型"""
        info = CollectionInfo(
            name="test_collection",
            vector_size=512,
            distance_metric=DistanceMetric.COSINE,
            vector_count=1000,
            index_type=IndexType.HNSW,
            description="Test collection"
        )
        assert info.name == "test_collection"
        assert info.vector_size == 512
        assert info.distance_metric == DistanceMetric.COSINE
        assert info.vector_count == 1000
        assert info.index_type == IndexType.HNSW
        assert info.description == "Test collection"

    def test_search_result(self):
        """测试SearchResult模型"""
        result = SearchResult(
            id="result1",
            score=0.95,
            vector=[0.1, 0.2, 0.3],
            payload={"match": True}
        )
        assert result.id == "result1"
        assert result.score == pytest.approx(0.95)
        assert result.vector == [0.1, 0.2, 0.3]
        assert result.payload == {"match": True}

        # 测试可选字段
        result_min = SearchResult(id="2", score=0.8)
        assert result_min.vector is None
        assert result_min.payload is None

    def test_search_params(self):
        """测试SearchParams模型"""
        # 基本参数
        params = SearchParams(
            collection_name="my_collection",
            query_vector=[0.1, 0.2, 0.3],
            limit=10,
            score_threshold=0.5,
            filter={"category": "test"},
            with_vectors=True,
            offset=20
        )
        assert params.collection_name == "my_collection"
        assert params.query_vector == [0.1, 0.2, 0.3]
        assert params.limit == 10
        assert params.score_threshold == 0.5
        assert params.filter == {"category": "test"}
        assert params.with_vectors is True
        assert params.offset == 20

        # 测试默认值
        params_default = SearchParams(
            collection_name="test",
            query_vector=[0.1, 0.2]
        )
        assert params_default.limit == 10
        assert params_default.score_threshold is None
        assert params_default.filter is None
        assert params_default.with_vectors is False
        assert params_default.offset is None

    def test_hybrid_search_params(self):
        """测试HybridSearchParams模型"""
        params = HybridSearchParams(
            collection_name="hybrid_collection",
            dense_vector=[0.1, 0.2, 0.3],
            sparse_vector={"word1": 1.0, "word2": 0.5},
            text_query="example query",
            limit=20,
            alpha=0.7,
            score_threshold=0.6,
            filter={"lang": "en"}
        )
        assert params.collection_name == "hybrid_collection"
        assert params.dense_vector == [0.1, 0.2, 0.3]
        assert params.sparse_vector == {"word1": 1.0, "word2": 0.5}
        assert params.text_query == "example query"
        assert params.limit == 20
        assert params.alpha == 0.7
        assert params.score_threshold == 0.6
        assert params.filter == {"lang": "en"}

        # 测试默认值
        params_default = HybridSearchParams(
            collection_name="test",
            dense_vector=[0.1, 0.2]
        )
        assert params_default.limit == 10
        assert params_default.alpha == 0.5
        assert params_default.sparse_vector is None
        assert params_default.text_query is None

    def test_collection_limit(self):
        """测试CollectionLimit模型"""
        limit = CollectionLimit(
            max_collections=100,
            max_vectors_per_collection=1000000,
            max_vector_size=4096,
            current_collections=50,
            current_vectors=500000
        )
        assert limit.max_collections == 100
        assert limit.max_vectors_per_collection == 1000000
        assert limit.max_vector_size == 4096
        assert limit.current_collections == 50
        assert limit.current_vectors == 500000

    def test_insert_params(self):
        """测试InsertParams模型"""
        data = [
            VectorData(id="1", vector=[0.1, 0.2]),
            VectorData(id="2", vector=[0.3, 0.4])
        ]
        params = InsertParams(
            collection_name="insert_test",
            data=data,
            batch_size=100
        )
        assert params.collection_name == "insert_test"
        assert params.data == data
        assert params.batch_size == 100

        # 测试可选batch_size
        params_no_batch = InsertParams(
            collection_name="test",
            data=data
        )
        assert params_no_batch.batch_size is None

    def test_delete_params(self):
        """测试DeleteParams模型"""
        # 使用ID删除
        params_ids = DeleteParams(
            collection_name="delete_test",
            ids=["id1", "id2", "id3"]
        )
        assert params_ids.collection_name == "delete_test"
        assert params_ids.ids == ["id1", "id2", "id3"]
        assert params_ids.filter is None

        # 使用过滤器删除
        params_filter = DeleteParams(
            collection_name="delete_test",
            filter={"category": "old"}
        )
        assert params_filter.filter == {"category": "old"}
        assert params_filter.ids is None

    def test_query_params(self):
        """测试QueryParams模型"""
        params = QueryParams(
            collection_name="query_test",
            filter={"status": "active"},
            limit=50,
            offset=100,
            with_vectors=True
        )
        assert params.collection_name == "query_test"
        assert params.filter == {"status": "active"}
        assert params.limit == 50
        assert params.offset == 100
        assert params.with_vectors is True

        # 测试默认值
        params_default = QueryParams(collection_name="test")
        assert params_default.filter is None
        assert params_default.limit is None
        assert params_default.offset is None
        assert params_default.with_vectors is False

    def test_distance_metric_enum(self):
        """测试距离度量枚举"""
        assert DistanceMetric.COSINE == "cosine"
        assert DistanceMetric.EUCLIDEAN == "euclidean"
        assert DistanceMetric.DOT_PRODUCT == "dot_product"
        assert DistanceMetric.HAMMING == "hamming"

    def test_index_type_enum(self):
        """测试索引类型枚举"""
        assert IndexType.FLAT == "flat"
        assert IndexType.IVF_FLAT == "ivf_flat"
        assert IndexType.IVF_SQ8 == "ivf_sq8"
        assert IndexType.IVF_PQ == "ivf_pq"
        assert IndexType.HNSW == "hnsw"