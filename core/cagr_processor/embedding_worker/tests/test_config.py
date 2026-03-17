import unittest
import os
from unittest.mock import patch

from embedding_worker.config import (
    VectorDBConfig, QdrantConfig, MilvusConfig
)
from embedding_worker.exceptions import ConfigException


class TestQdrantConfig(unittest.TestCase):
    """测试Qdrant配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = QdrantConfig()
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 6333)
        self.assertIsNone(config.url)
        self.assertIsNone(config.api_key)
        self.assertFalse(config.prefer_grpc)

    def test_custom_config(self):
        """测试自定义配置"""
        config = QdrantConfig(
            host="192.168.1.100",
            port=6334,
            url="http://qdrant.example.com",
            api_key="test-key",
            prefer_grpc=True
        )
        self.assertEqual(config.host, "192.168.1.100")
        self.assertEqual(config.port, 6334)
        self.assertEqual(config.url, "http://qdrant.example.com")
        self.assertEqual(config.api_key, "test-key")
        self.assertTrue(config.prefer_grpc)


class TestMilvusConfig(unittest.TestCase):
    """测试Milvus配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = MilvusConfig()
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 19530)
        self.assertEqual(config.db_name, "default")
        self.assertFalse(config.secure)

    def test_custom_config(self):
        """测试自定义配置"""
        config = MilvusConfig(
            host="192.168.1.100",
            port=19531,
            uri="http://milvus.example.com",
            user="admin",
            password="secret",
            db_name="my_db",
            secure=True
        )
        self.assertEqual(config.host, "192.168.1.100")
        self.assertEqual(config.port, 19531)
        self.assertEqual(config.uri, "http://milvus.example.com")
        self.assertEqual(config.user, "admin")
        self.assertEqual(config.password, "secret")
        self.assertEqual(config.db_name, "my_db")
        self.assertTrue(config.secure)


class TestVectorDBConfig(unittest.TestCase):
    """测试向量数据库配置"""

    def test_qdrant_config_creation(self):
        """测试创建Qdrant配置"""
        qdrant_config = QdrantConfig(host="localhost", port=6333)
        config = VectorDBConfig(
            db_type="qdrant",
            qdrant_config=qdrant_config,
            max_connections=20
        )
        self.assertEqual(config.db_type, "qdrant")
        self.assertEqual(config.qdrant_config, qdrant_config)
        self.assertEqual(config.max_connections, 20)

    def test_milvus_config_creation(self):
        """测试创建Milvus配置"""
        milvus_config = MilvusConfig(host="localhost", port=19530)
        config = VectorDBConfig(
            db_type="milvus",
            milvus_config=milvus_config,
            operation_timeout=60.0
        )
        self.assertEqual(config.db_type, "milvus")
        self.assertEqual(config.milvus_config, milvus_config)
        self.assertEqual(config.operation_timeout, 60.0)

    def test_validate_success(self):
        """测试配置验证成功"""
        config = VectorDBConfig(
            db_type="qdrant",
            qdrant_config=QdrantConfig()
        )
        # 应该不抛出异常
        config.validate()

    def test_validate_invalid_db_type(self):
        """测试无效的数据库类型"""
        config = VectorDBConfig(
            db_type="invalid_db",
            qdrant_config=QdrantConfig()
        )
        # 现在支持动态注册，所以不抛出异常
        config.validate()  # 应该不抛出异常

    def test_validate_missing_config(self):
        """测试缺少配置"""
        config = VectorDBConfig(db_type="qdrant")
        with self.assertRaises(ValueError):
            config.validate()

    @patch.dict(os.environ, {
        "VECTOR_DB_TYPE": "qdrant",
        "QDRANT_HOST": "test-host",
        "QDRANT_PORT": "9999",
        "QDRANT_API_KEY": "test-key",
    })
    def test_from_env_qdrant(self):
        """测试从环境变量加载Qdrant配置"""
        config = VectorDBConfig.from_env()
        self.assertEqual(config.db_type, "qdrant")
        self.assertEqual(config.qdrant_config.host, "test-host")
        self.assertEqual(config.qdrant_config.port, 9999)
        self.assertEqual(config.qdrant_config.api_key, "test-key")

    @patch.dict(os.environ, {
        "VECTOR_DB_TYPE": "milvus",
        "MILVUS_HOST": "test-milvus",
        "MILVUS_PORT": "8888",
        "MILVUS_USER": "test-user",
        "MILVUS_PASSWORD": "test-pass",
    })
    def test_from_env_milvus(self):
        """测试从环境变量加载Milvus配置"""
        config = VectorDBConfig.from_env()
        self.assertEqual(config.db_type, "milvus")
        self.assertEqual(config.milvus_config.host, "test-milvus")
        self.assertEqual(config.milvus_config.port, 8888)
        self.assertEqual(config.milvus_config.user, "test-user")
        self.assertEqual(config.milvus_config.password, "test-pass")

    @patch.dict(os.environ, {"VECTOR_DB_TYPE": "unsupported"})
    def test_from_env_unsupported(self):
        """测试不支持的数据库类型"""
        with self.assertRaises(ValueError):
            VectorDBConfig.from_env()


if __name__ == "__main__":
    unittest.main()