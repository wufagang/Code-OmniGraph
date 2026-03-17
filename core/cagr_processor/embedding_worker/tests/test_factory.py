import unittest
from unittest.mock import Mock, patch

from embedding_worker.factory import VectorDBFactory
from embedding_worker.config import VectorDBConfig, QdrantConfig, MilvusConfig
from embedding_worker.interfaces import VectorDatabase
from embedding_worker.exceptions import ConfigException


class MockVectorDB(VectorDatabase):
    """用于测试的模拟向量数据库实现"""
    def __init__(self, config):
        self.config = config
        self.connected = True

    def create_collection(self, *args, **kwargs):
        return True

    def create_hybrid_collection(self, *args, **kwargs):
        return True

    def insert(self, *args, **kwargs):
        return 1

    def search(self, *args, **kwargs):
        return []

    def delete(self, *args, **kwargs):
        return 1

    def drop_collection(self, collection_name: str) -> bool:
        return True

    def has_collection(self, collection_name: str) -> bool:
        return True

    def list_collections(self):
        return []

    def get_collection_info(self, collection_name: str):
        from embedding_worker.models import CollectionInfo, DistanceMetric
        return CollectionInfo(
            name=collection_name,
            vector_size=768,
            distance_metric=DistanceMetric.COSINE
        )

    def insert_hybrid(self, *args, **kwargs):
        return 1

    def hybrid_search(self, *args, **kwargs):
        return []

    def query(self, *args, **kwargs):
        return []

    def check_collection_limit(self, collection_name: str):
        from embedding_worker.models import CollectionLimit
        return CollectionLimit()

    def close(self):
        self.connected = False


class TestVectorDBFactory(unittest.TestCase):
    """测试向量数据库工厂"""

    def setUp(self):
        """测试前准备"""
        # 保存原始注册表
        self.original_registry = VectorDBFactory._registry.copy()

    def tearDown(self):
        """测试后清理"""
        # 恢复原始注册表
        VectorDBFactory._registry = self.original_registry

    def test_register_new_implementation(self):
        """测试注册新的实现"""
        # 注册新的实现
        VectorDBFactory.register("mock", MockVectorDB)

        # 验证注册成功
        self.assertIn("mock", VectorDBFactory._registry)
        self.assertEqual(VectorDBFactory._registry["mock"], MockVectorDB)

    @patch('embedding_worker.factory.QdrantDatabase')
    def test_create_qdrant(self, mock_qdrant_class):
        """测试创建Qdrant实例"""
        config = VectorDBConfig(
            db_type="qdrant",
            qdrant_config=QdrantConfig()
        )

        mock_instance = Mock()
        mock_qdrant_class.return_value = mock_instance

        # 模拟QDRANT_AVAILABLE为True
        with patch('embedding_worker.impl.qdrant_impl.QDRANT_AVAILABLE', True):
            result = VectorDBFactory.create(config)

        mock_qdrant_class.assert_called_once_with(config)
        self.assertEqual(result, mock_instance)

    @patch('embedding_worker.factory.MilvusDatabase')
    def test_create_milvus(self, mock_milvus_class):
        """测试创建Milvus实例"""
        config = VectorDBConfig(
            db_type="milvus",
            milvus_config=MilvusConfig()
        )

        mock_instance = Mock()
        mock_milvus_class.return_value = mock_instance

        # 模拟MILVUS_AVAILABLE为True
        with patch('embedding_worker.impl.milvus_impl.MILVUS_AVAILABLE', True):
            result = VectorDBFactory.create(config)

        mock_milvus_class.assert_called_once_with(config)
        self.assertEqual(result, mock_instance)

    def test_create_unsupported_type(self):
        """测试创建不支持的数据库类型"""
        config = VectorDBConfig(
            db_type="unsupported",
            qdrant_config=QdrantConfig()
        )

        with self.assertRaises(ConfigException) as context:
            VectorDBFactory.create(config)

        self.assertIn("Unsupported vector database type", str(context.exception))
        # 现在支持动态注册，所以不会列出支持的类型

    @patch('embedding_worker.factory.QdrantDatabase')
    def test_create_from_config_dict_qdrant(self, mock_qdrant_class):
        """测试从配置字典创建Qdrant实例"""
        config_dict = {
            "db_type": "qdrant",
            "qdrant_config": {
                "host": "localhost",
                "port": 6333
            },
            "max_connections": 20
        }

        mock_instance = Mock()
        mock_qdrant_class.return_value = mock_instance

        # 模拟QDRANT_AVAILABLE为True
        with patch('embedding_worker.impl.qdrant_impl.QDRANT_AVAILABLE', True):
            result = VectorDBFactory.create_from_config_dict(config_dict)

        # 验证创建配置对象时参数正确
        call_args = mock_qdrant_class.call_args[0][0]
        self.assertEqual(call_args.db_type, "qdrant")
        self.assertEqual(call_args.qdrant_config.host, "localhost")
        self.assertEqual(call_args.qdrant_config.port, 6333)
        self.assertEqual(call_args.max_connections, 20)

        self.assertEqual(result, mock_instance)

    @patch('embedding_worker.factory.MilvusDatabase')
    def test_create_from_config_dict_milvus(self, mock_milvus_class):
        """测试从配置字典创建Milvus实例"""
        config_dict = {
            "db_type": "milvus",
            "milvus_config": {
                "host": "localhost",
                "port": 19530,
                "user": "admin",
                "password": "secret"
            }
        }

        mock_instance = Mock()
        mock_milvus_class.return_value = mock_instance

        # 模拟MILVUS_AVAILABLE为True
        with patch('embedding_worker.impl.milvus_impl.MILVUS_AVAILABLE', True):
            result = VectorDBFactory.create_from_config_dict(config_dict)

        call_args = mock_milvus_class.call_args[0][0]
        self.assertEqual(call_args.db_type, "milvus")
        self.assertEqual(call_args.milvus_config.host, "localhost")
        self.assertEqual(call_args.milvus_config.port, 19530)
        self.assertEqual(call_args.milvus_config.user, "admin")
        self.assertEqual(call_args.milvus_config.password, "secret")

        self.assertEqual(result, mock_instance)

    def test_create_from_config_dict_invalid_type(self):
        """测试从配置字典创建不支持的类型"""
        config_dict = {
            "db_type": "unknown"
        }

        with self.assertRaises(ConfigException) as context:
            VectorDBFactory.create_from_config_dict(config_dict)

        self.assertIn("Unsupported db_type", str(context.exception))

    @patch('embedding_worker.factory.VectorDBConfig.from_env')
    @patch('embedding_worker.factory.QdrantDatabase')
    def test_create_from_env(self, mock_qdrant_class, mock_from_env):
        """测试从环境变量创建"""
        with patch.dict('os.environ', {
            'VECTOR_DB_TYPE': 'qdrant',
            'QDRANT_HOST': 'env-host',
            'QDRANT_PORT': '7777'
        }):
            mock_config = VectorDBConfig(
                db_type="qdrant",
                qdrant_config=QdrantConfig(host="env-host", port=7777)
            )
            mock_from_env.return_value = mock_config

            mock_instance = Mock()
            mock_qdrant_class.return_value = mock_instance

            # 模拟QDRANT_AVAILABLE为True
            with patch('embedding_worker.impl.qdrant_impl.QDRANT_AVAILABLE', True):
                result = VectorDBFactory.create_from_env()

            mock_from_env.assert_called_once()
            mock_qdrant_class.assert_called_once_with(mock_config)
            self.assertEqual(result, mock_instance)

    def test_get_supported_types(self):
        """测试获取支持的数据库类型"""
        supported = VectorDBFactory.get_supported_types()
        self.assertIn("qdrant", supported)
        self.assertIn("milvus", supported)
        self.assertIsInstance(supported, list)

    def test_is_supported(self):
        """测试检查是否支持指定类型"""
        self.assertTrue(VectorDBFactory.is_supported("qdrant"))
        self.assertTrue(VectorDBFactory.is_supported("milvus"))
        self.assertTrue(VectorDBFactory.is_supported("QDRANT"))  # 大小写不敏感
        self.assertTrue(VectorDBFactory.is_supported("Milvus"))
        self.assertFalse(VectorDBFactory.is_supported("unknown"))
        self.assertFalse(VectorDBFactory.is_supported(""))

    def test_create_with_mock_implementation(self):
        """测试使用模拟实现创建实例"""
        # 注册模拟实现
        VectorDBFactory.register("mock", MockVectorDB)

        # 创建一个有效的配置
        config = VectorDBConfig(
            db_type="mock",
            qdrant_config=QdrantConfig(),  # 提供qdrant_config，虽然不会被使用
            max_connections=100
        )

        result = VectorDBFactory.create(config)

        self.assertIsInstance(result, MockVectorDB)
        self.assertEqual(result.config, config)
        self.assertTrue(result.connected)

        # 测试关闭
        result.close()
        self.assertFalse(result.connected)


if __name__ == "__main__":
    unittest.main()