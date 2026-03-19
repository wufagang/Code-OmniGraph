import pytest
import os
from unittest.mock import patch

from cagr_processor.embedding_dao.config import (
    VectorDBConfig, QdrantConfig, MilvusConfig
)
from cagr_common.exceptions import VectorConfigException


class TestQdrantConfig:
    """测试Qdrant配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = QdrantConfig()
        assert config.host == "localhost"
        assert config.port == 6333
        assert config.url is None
        assert config.api_key is None
        assert config.prefer_grpc is False

    def test_custom_config(self):
        """测试自定义配置"""
        config = QdrantConfig(
            host="192.168.1.100",
            port=6334,
            url="http://qdrant.example.com",
            api_key="test-key",
            prefer_grpc=True
        )
        assert config.host == "192.168.1.100"
        assert config.port == 6334
        assert config.url == "http://qdrant.example.com"
        assert config.api_key == "test-key"
        assert config.prefer_grpc is True


class TestMilvusConfig:
    """测试Milvus配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = MilvusConfig()
        assert config.host == "localhost"
        assert config.port == 19530
        assert config.db_name == "default"
        assert config.secure is False

    def test_custom_config(self):
        """测试自定义配置"""
        config = MilvusConfig(
            host="192.168.1.200",
            port=19531,
            db_name="test_db",
            secure=True,
            user="user",
            password="pass"
        )
        assert config.host == "192.168.1.200"
        assert config.port == 19531
        assert config.db_name == "test_db"
        assert config.secure is True
        assert config.user == "user"
        assert config.password == "pass"


class TestVectorDBConfig:
    """测试通用向量数据库配置"""

    def test_from_env_qdrant(self):
        """测试从环境变量创建Qdrant配置"""
        env_vars = {
            "VECTOR_DB_TYPE": "qdrant",
            "QDRANT_HOST": "test-host",
            "QDRANT_PORT": "9999",
            "QDRANT_API_KEY": "test-api-key",
            "QDRANT_PREFER_GRPC": "true"
        }

        with patch.dict(os.environ, env_vars):
            config = VectorDBConfig.from_env()

            assert isinstance(config, VectorDBConfig)
            assert config.db_type == "qdrant"
            assert config.qdrant_config.host == "test-host"
            assert config.qdrant_config.port == 9999
            assert config.qdrant_config.api_key == "test-api-key"
            assert config.qdrant_config.prefer_grpc is True

    def test_from_env_milvus(self):
        """测试从环境变量创建Milvus配置"""
        env_vars = {
            "VECTOR_DB_TYPE": "milvus",
            "MILVUS_HOST": "test-host",
            "MILVUS_PORT": "8888",
            "MILVUS_DB_NAME": "test_db",
            "MILVUS_SECURE": "true",
            "MILVUS_USER": "test-user",
            "MILVUS_PASSWORD": "test-pass"
        }

        with patch.dict(os.environ, env_vars):
            config = VectorDBConfig.from_env()

            assert isinstance(config, VectorDBConfig)
            assert config.db_type == "milvus"
            assert config.milvus_config.host == "test-host"
            assert config.milvus_config.port == 8888
            assert config.milvus_config.db_name == "test_db"
            assert config.milvus_config.secure is True
            assert config.milvus_config.user == "test-user"
            assert config.milvus_config.password == "test-pass"

    def test_from_env_unsupported_type(self):
        """测试不支持的数据库类型"""
        env_vars = {
            "VECTOR_DB_TYPE": "unsupported_db"
        }

        with patch.dict(os.environ, env_vars):
            with pytest.raises(ValueError) as exc_info:
                VectorDBConfig.from_env()

            assert "Unsupported vector database type" in str(exc_info.value)

    def test_from_env_default_qdrant(self):
        """测试默认使用Qdrant"""
        # 不设置VECTOR_DB_TYPE
        with patch.dict(os.environ, {}, clear=True):
            config = VectorDBConfig.from_env()

            assert isinstance(config, VectorDBConfig)
            assert config.db_type == "qdrant"
            assert config.qdrant_config.host == "localhost"
            assert config.qdrant_config.port == 6333

    def test_config_validation(self):
        """测试配置验证"""
        # Qdrant配置验证
        config = QdrantConfig(host="", port=6333)
        # 这里可以添加验证逻辑，如果有的话

        # Milvus配置验证
        config = MilvusConfig(host="localhost", port=0)
        # 这里可以添加验证逻辑，如果有的话

    def test_config_to_dict(self):
        """测试配置转换为字典"""
        config = QdrantConfig(
            host="test-host",
            port=1234,
            api_key="test-key"
        )

        config_dict = config.dict() if hasattr(config, 'dict') else config.__dict__

        assert "host" in config_dict
        assert "port" in config_dict
        assert config_dict["host"] == "test-host"
        assert config_dict["port"] == 1234