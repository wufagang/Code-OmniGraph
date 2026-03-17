import unittest
from dataclasses import dataclass

from embedding_worker.models import (
    VectorData, CollectionInfo, SearchResult, SearchParams,
    HybridSearchParams, CollectionLimit, DistanceMetric, IndexType,
    InsertParams, DeleteParams, QueryParams
)


class TestModels(unittest.TestCase):
    """测试数据模型"""

    def test_vector_data(self):
        """测试VectorData模型"""
        # 基本测试
        data = VectorData(
            id="test_id",
            vector=[0.1, 0.2, 0.3],
            payload={"key": "value"}
        )
        self.assertEqual(data.id, "test_id")
        self.assertEqual(data.vector, [0.1, 0.2, 0.3])
        self.assertEqual(data.payload, {"key": "value"})

        # 测试可选payload
        data_no_payload = VectorData(id="1", vector=[1.0, 2.0])
        self.assertIsNone(data_no_payload.payload)

        # 测试数字ID
        data_numeric = VectorData(id=123, vector=[0.1, 0.2])
        self.assertEqual(data_numeric.id, 123)

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
        self.assertEqual(info.name, "test_collection")
        self.assertEqual(info.vector_size, 512)
        self.assertEqual(info.distance_metric, DistanceMetric.COSINE)
        self.assertEqual(info.vector_count, 1000)
        self.assertEqual(info.index_type, IndexType.HNSW)
        self.assertEqual(info.description, "Test collection")

    def test_search_result(self):
        """测试SearchResult模型"""
        result = SearchResult(
            id="result1",
            score=0.95,
            vector=[0.1, 0.2, 0.3],
            payload={"match": True}
        )
        self.assertEqual(result.id, "result1")
        self.assertAlmostEqual(result.score, 0.95)
        self.assertEqual(result.vector, [0.1, 0.2, 0.3])
        self.assertEqual(result.payload, {"match": True})

        # 测试可选字段
        result_min = SearchResult(id="2", score=0.8)
        self.assertIsNone(result_min.vector)
        self.assertIsNone(result_min.payload)

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
        self.assertEqual(params.collection_name, "my_collection")
        self.assertEqual(params.query_vector, [0.1, 0.2, 0.3])
        self.assertEqual(params.limit, 10)
        self.assertEqual(params.score_threshold, 0.5)
        self.assertEqual(params.filter, {"category": "test"})
        self.assertTrue(params.with_vectors)
        self.assertEqual(params.offset, 20)

        # 测试默认值
        params_default = SearchParams(
            collection_name="test",
            query_vector=[0.1, 0.2]
        )
        self.assertEqual(params_default.limit, 10)
        self.assertIsNone(params_default.score_threshold)
        self.assertIsNone(params_default.filter)
        self.assertFalse(params_default.with_vectors)
        self.assertIsNone(params_default.offset)

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
        self.assertEqual(params.collection_name, "hybrid_collection")
        self.assertEqual(params.dense_vector, [0.1, 0.2, 0.3])
        self.assertEqual(params.sparse_vector, {"word1": 1.0, "word2": 0.5})
        self.assertEqual(params.text_query, "example query")
        self.assertEqual(params.limit, 20)
        self.assertEqual(params.alpha, 0.7)
        self.assertEqual(params.score_threshold, 0.6)
        self.assertEqual(params.filter, {"lang": "en"})

        # 测试默认值
        params_default = HybridSearchParams(
            collection_name="test",
            dense_vector=[0.1, 0.2]
        )
        self.assertEqual(params_default.limit, 10)
        self.assertEqual(params_default.alpha, 0.5)
        self.assertIsNone(params_default.sparse_vector)
        self.assertIsNone(params_default.text_query)

    def test_collection_limit(self):
        """测试CollectionLimit模型"""
        limit = CollectionLimit(
            max_collections=100,
            max_vectors_per_collection=1000000,
            max_vector_size=4096,
            current_collections=50,
            current_vectors=500000
        )
        self.assertEqual(limit.max_collections, 100)
        self.assertEqual(limit.max_vectors_per_collection, 1000000)
        self.assertEqual(limit.max_vector_size, 4096)
        self.assertEqual(limit.current_collections, 50)
        self.assertEqual(limit.current_vectors, 500000)

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
        self.assertEqual(params.collection_name, "insert_test")
        self.assertEqual(params.data, data)
        self.assertEqual(params.batch_size, 100)

        # 测试可选batch_size
        params_no_batch = InsertParams(
            collection_name="test",
            data=data
        )
        self.assertIsNone(params_no_batch.batch_size)

    def test_delete_params(self):
        """测试DeleteParams模型"""
        # 使用ID删除
        params_ids = DeleteParams(
            collection_name="delete_test",
            ids=["id1", "id2", "id3"]
        )
        self.assertEqual(params_ids.collection_name, "delete_test")
        self.assertEqual(params_ids.ids, ["id1", "id2", "id3"])
        self.assertIsNone(params_ids.filter)

        # 使用过滤器删除
        params_filter = DeleteParams(
            collection_name="delete_test",
            filter={"category": "old"}
        )
        self.assertEqual(params_filter.filter, {"category": "old"})
        self.assertIsNone(params_filter.ids)

    def test_query_params(self):
        """测试QueryParams模型"""
        params = QueryParams(
            collection_name="query_test",
            filter={"status": "active"},
            limit=50,
            offset=100,
            with_vectors=True
        )
        self.assertEqual(params.collection_name, "query_test")
        self.assertEqual(params.filter, {"status": "active"})
        self.assertEqual(params.limit, 50)
        self.assertEqual(params.offset, 100)
        self.assertTrue(params.with_vectors)

        # 测试默认值
        params_default = QueryParams(collection_name="test")
        self.assertIsNone(params_default.filter)
        self.assertIsNone(params_default.limit)
        self.assertIsNone(params_default.offset)
        self.assertFalse(params_default.with_vectors)

    def test_distance_metric_enum(self):
        """测试距离度量枚举"""
        self.assertEqual(DistanceMetric.COSINE, "cosine")
        self.assertEqual(DistanceMetric.EUCLIDEAN, "euclidean")
        self.assertEqual(DistanceMetric.DOT_PRODUCT, "dot_product")
        self.assertEqual(DistanceMetric.HAMMING, "hamming")

    def test_index_type_enum(self):
        """测试索引类型枚举"""
        self.assertEqual(IndexType.FLAT, "flat")
        self.assertEqual(IndexType.IVF_FLAT, "ivf_flat")
        self.assertEqual(IndexType.IVF_SQ8, "ivf_sq8")
        self.assertEqual(IndexType.IVF_PQ, "ivf_pq")
        self.assertEqual(IndexType.HNSW, "hnsw")


if __name__ == "__main__":
    unittest.main()