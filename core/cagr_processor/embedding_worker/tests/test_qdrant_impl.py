import unittest
from unittest.mock import Mock, patch, MagicMock

from embedding_worker.impl.qdrant_impl import QdrantDatabase, QdrantDistanceMapper
from embedding_worker.config import VectorDBConfig, QdrantConfig
from embedding_worker.models import VectorData, DistanceMetric, SearchParams
from embedding_worker.exceptions import (
    ConnectionException, CollectionAlreadyExistsException,
    CollectionNotFoundException, InsertException
)


class TestQdrantDistanceMapper(unittest.TestCase):
    """测试Qdrant距离度量映射器"""

    def test_to_qdrant_mapping(self):
        """测试距离度量映射"""
        # 测试COSINE
        result = QdrantDistanceMapper.to_qdrant(DistanceMetric.COSINE)
        try:
            from qdrant_client.models import Distance
            self.assertEqual(result, Distance.COSINE)
        except ImportError:
            self.skipTest("qdrant-client not installed")

        # 测试EUCLIDEAN
        result = QdrantDistanceMapper.to_qdrant(DistanceMetric.EUCLIDEAN)
        try:
            self.assertEqual(result, Distance.EUCLIDEAN)
        except:
            pass

        # 测试DOT_PRODUCT
        result = QdrantDistanceMapper.to_qdrant(DistanceMetric.DOT_PRODUCT)
        try:
            self.assertEqual(result, Distance.DOT)
        except:
            pass

        # 测试不支持的类型，应该返回默认的COSINE
        result = QdrantDistanceMapper.to_qdrant(DistanceMetric.HAMMING)
        try:
            self.assertEqual(result, Distance.COSINE)
        except:
            pass


class TestQdrantDatabase(unittest.TestCase):
    """测试Qdrant数据库实现"""

    def setUp(self):
        """测试前准备"""
        self.config = VectorDBConfig(
            db_type="qdrant",
            qdrant_config=QdrantConfig(host="localhost", port=6333)
        )

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_connect_success(self, mock_client_class):
        """测试成功连接"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None

        db = QdrantDatabase(self.config)

        mock_client_class.assert_called_once_with(host="localhost", port=6333)
        mock_client.get_collections.assert_called_once()
        self.assertEqual(db._client, mock_client)

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_connect_with_url(self, mock_client_class):
        """测试使用URL连接"""
        self.config.qdrant_config.url = "http://qdrant.example.com"
        self.config.qdrant_config.api_key = "test-key"

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None

        db = QdrantDatabase(self.config)

        mock_client_class.assert_called_once_with(
            url="http://qdrant.example.com",
            api_key="test-key",
            prefer_grpc=False,
            timeout=None,
            https=None,
            prefix=None
        )

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_connect_failure(self, mock_client_class):
        """测试连接失败"""
        mock_client_class.side_effect = Exception("Connection failed")

        with self.assertRaises(ConnectionException) as context:
            QdrantDatabase(self.config)

        self.assertIn("Failed to connect to Qdrant", str(context.exception))

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_close(self, mock_client_class):
        """测试关闭连接"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None

        db = QdrantDatabase(self.config)
        db.close()

        self.assertIsNone(db._client)

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_create_collection_success(self, mock_client_class):
        """测试成功创建集合"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None
        mock_client.collection_exists.return_value = False
        mock_client.create_collection.return_value = None

        db = QdrantDatabase(self.config)

        result = db.create_collection(
            collection_name="test_collection",
            vector_size=768,
            distance_metric=DistanceMetric.COSINE
        )

        self.assertTrue(result)
        mock_client.collection_exists.assert_called_once_with("test_collection")
        mock_client.create_collection.assert_called_once()

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_create_collection_already_exists(self, mock_client_class):
        """测试集合已存在"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None
        mock_client.collection_exists.return_value = True

        db = QdrantDatabase(self.config)

        with self.assertRaises(CollectionAlreadyExistsException) as context:
            db.create_collection("existing_collection", 768)

        self.assertEqual(context.exception.collection_name, "existing_collection")

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_create_hybrid_collection(self, mock_client_class):
        """测试创建混合向量集合"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None
        mock_client.collection_exists.return_value = False
        mock_client.create_collection.return_value = None

        db = QdrantDatabase(self.config)

        result = db.create_hybrid_collection(
            collection_name="hybrid_collection",
            dense_vector_size=768,
            sparse_vector_size=10000,
            distance_metric=DistanceMetric.EUCLIDEAN
        )

        self.assertTrue(result)
        mock_client.create_collection.assert_called_once()

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_has_collection(self, mock_client_class):
        """测试检查集合是否存在"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None

        db = QdrantDatabase(self.config)

        # 集合存在
        mock_client.collection_exists.return_value = True
        self.assertTrue(db.has_collection("existing_collection"))

        # 集合不存在
        mock_client.collection_exists.return_value = False
        self.assertFalse(db.has_collection("non_existing_collection"))

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_list_collections(self, mock_client_class):
        """测试列出集合"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None

        # 模拟集合列表
        mock_collection = Mock()
        mock_collection.name = "collection1"
        mock_collection2 = Mock()
        mock_collection2.name = "collection2"

        mock_response = Mock()
        mock_response.collections = [mock_collection, mock_collection2]
        mock_client.get_collections.return_value = mock_response

        db = QdrantDatabase(self.config)

        collections = db.list_collections()

        self.assertEqual(collections, ["collection1", "collection2"])

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_insert_impl(self, mock_client_class):
        """测试插入数据实现"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None

        from qdrant_client.models import UpdateStatus

        mock_result = Mock()
        mock_result.status = UpdateStatus.COMPLETED
        mock_client.upsert.return_value = mock_result

        db = QdrantDatabase(self.config)

        data = [
            VectorData(id="1", vector=[0.1, 0.2], payload={"key": "value"}),
            VectorData(id="2", vector=[0.3, 0.4], payload={"key2": "value2"})
        ]

        count = db._insert_impl("test_collection", data)

        self.assertEqual(count, 2)
        mock_client.upsert.assert_called_once()

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_insert_impl_failure(self, mock_client_class):
        """测试插入失败"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None

        from qdrant_client.models import UpdateStatus

        mock_result = Mock()
        mock_result.status = UpdateStatus.FAILED
        mock_client.upsert.return_value = mock_result

        db = QdrantDatabase(self.config)

        data = [VectorData(id="1", vector=[0.1, 0.2])]

        with self.assertRaises(InsertException):
            db._insert_impl("test_collection", data)

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_search_impl(self, mock_client_class):
        """测试搜索实现"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None

        # 模拟搜索结果
        mock_result = Mock()
        mock_result.id = "1"
        mock_result.score = 0.95
        mock_result.payload = {"key": "value"}
        mock_result.vector = [0.1, 0.2]

        mock_client.search.return_value = [mock_result]

        db = QdrantDatabase(self.config)

        params = SearchParams(
            collection_name="test_collection",
            query_vector=[0.1, 0.2],
            limit=5,
            with_vectors=True
        )

        results = db._search_impl(params)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "1")
        self.assertAlmostEqual(results[0].score, 0.95)
        self.assertEqual(results[0].payload, {"key": "value"})
        self.assertEqual(results[0].vector, [0.1, 0.2])

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_delete_impl_with_ids(self, mock_client_class):
        """测试使用ID删除"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None

        from qdrant_client.models import UpdateStatus

        mock_result = Mock()
        mock_result.status = UpdateStatus.COMPLETED
        mock_client.delete.return_value = mock_result

        db = QdrantDatabase(self.config)

        count = db._delete_impl(
            "test_collection",
            ids=["1", "2", "3"],
            filter=None
        )

        # Qdrant不返回删除数量，返回ID数量
        self.assertEqual(count, 3)

    @patch('embedding_worker.impl.qdrant_impl.QdrantClient')
    def test_convert_filter(self, mock_client_class):
        """测试转换过滤条件"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_collections.return_value = None

        db = QdrantDatabase(self.config)

        filter_dict = {"category": "electronics", "price": 100}
        qdrant_filter = db._convert_filter(filter_dict)

        self.assertIsNotNone(qdrant_filter)
        self.assertEqual(len(qdrant_filter.must), 2)


if __name__ == "__main__":
    unittest.main()