import pytest
from unittest.mock import Mock, patch

from cagr_processor.embedding_worker.factory import VectorDBFactory
from cagr_processor.embedding_worker.config import VectorDBConfig, QdrantConfig, MilvusConfig
from cagr_processor.embedding_worker.interfaces import VectorDatabase
from cagr_common.exceptions import VectorConfigException


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
        from cagr_processor.embedding_worker.models import CollectionInfo, DistanceMetric
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
        from cagr_processor.embedding_worker.models import CollectionLimit
        return CollectionLimit()

    def close(self):
        self.connected = False


class TestVectorDBFactory:
    """测试VectorDBFactory"""

    def setup_method(self):
        """测试前准备"""
        # 清空注册表
        VectorDBFactory._registry.clear()

    def teardown_method(self):
        """测试后清理"""
        # 恢复注册表
        VectorDBFactory._registry.clear()

    def test_register_implementation(self):
        """测试注册实现"""
        # 注册模拟实现
        VectorDBFactory.register("mock", MockVectorDB)

        assert "mock" in VectorDBFactory._registry
        assert VectorDBFactory._registry["mock"] == MockVectorDB

    def test_create_with_registered_type(self):
        """测试使用已注册的类型创建"""
        # 注册实现
        VectorDBFactory.register("mock", MockVectorDB)

        # 创建配置
        config = VectorDBConfig(db_type="mock")

        # 创建实例
        instance = VectorDBFactory.create(config)

        assert isinstance(instance, MockVectorDB)
        assert instance.config == config

    def test_create_with_unregistered_type(self):
        """测试使用未注册的类型创建"""
        config = VectorDBConfig(db_type="unregistered")

        with pytest.raises(VectorConfigException) as exc_info:
            VectorDBFactory.create(config)

        assert "Unsupported vector database type" in str(exc_info.value)

    def test_create_with_qdrant_config(self):
        """测试使用Qdrant配置创建"""
        # 保存原始注册表状态
        original_registry = VectorDBFactory._registry.copy()

        # 重新注册qdrant，因为它在setup_method中被清空了
        from cagr_processor.embedding_worker.impl.qdrant_impl import QdrantDatabase
        VectorDBFactory.register("qdrant", QdrantDatabase)

        qdrant_config = QdrantConfig(host="localhost", port=6333)
        config = VectorDBConfig(db_type="qdrant", qdrant_config=qdrant_config)

        # 由于我们没有运行Qdrant服务，期望连接失败
        with pytest.raises(VectorConfigException) as exc_info:
            VectorDBFactory.create(config)

        # 应该是因为连接失败
        error_msg = str(exc_info.value)
        assert ("Failed to connect to Qdrant" in error_msg or
                "Failed to create vector database instance" in error_msg)

        # 恢复原始注册表状态
        VectorDBFactory._registry = original_registry

    def test_create_with_milvus_config(self):
        """测试使用Milvus配置创建"""
        config = MilvusConfig(host="localhost", port=19530)

        # 这应该会失败，因为milvus可能没有注册
        with pytest.raises(VectorConfigException):
            VectorDBFactory.create(config)

    def test_register_multiple_types(self):
        """测试注册多种类型"""
        # 创建多个模拟实现
        class MockVectorDB2(VectorDatabase):
            def __init__(self, config):
                self.config = config

        # 注册多个
        VectorDBFactory.register("mock1", MockVectorDB)
        VectorDBFactory.register("mock2", MockVectorDB2)

        assert len(VectorDBFactory._registry) == 2
        assert "mock1" in VectorDBFactory._registry
        assert "mock2" in VectorDBFactory._registry

    def test_create_with_different_configs(self):
        """测试使用不同配置创建"""
        VectorDBFactory.register("mock", MockVectorDB)

        # 测试不同配置
        config1 = VectorDBConfig(db_type="mock")
        config2 = VectorDBConfig(db_type="mock", max_connections=20)

        instance1 = VectorDBFactory.create(config1)
        instance2 = VectorDBFactory.create(config2)

        assert isinstance(instance1, MockVectorDB)
        assert isinstance(instance2, MockVectorDB)
        assert instance1 != instance2

    def test_factory_singleton_behavior(self):
        """测试工厂单例行为"""
        VectorDBFactory.register("mock", MockVectorDB)

        config = VectorDBConfig(db_type="mock")

        # 多次创建应该是不同的实例
        instance1 = VectorDBFactory.create(config)
        instance2 = VectorDBFactory.create(config)

        assert instance1 is not instance2
        assert isinstance(instance1, MockVectorDB)
        assert isinstance(instance2, MockVectorDB)

    def test_register_override(self):
        """测试注册覆盖"""
        # MockVectorDB2需要实现所有抽象方法
        class MockVectorDB2(VectorDatabase):
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
                from cagr_processor.embedding_worker.models import CollectionInfo, DistanceMetric
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
                from cagr_processor.embedding_worker.models import CollectionLimit
                return CollectionLimit()
            def close(self):
                self.connected = False

        # 注册第一个
        VectorDBFactory.register("mock", MockVectorDB)

        # 注册第二个，覆盖第一个
        VectorDBFactory.register("mock", MockVectorDB2)

        config = VectorDBConfig(db_type="mock")
        instance = VectorDBFactory.create(config)

        assert isinstance(instance, MockVectorDB2)
        assert not isinstance(instance, MockVectorDB)

    def test_empty_registry(self):
        """测试空注册表"""
        # 确保注册表为空
        VectorDBFactory._registry.clear()

        config = VectorDBConfig(db_type="any")

        with pytest.raises(VectorConfigException):
            VectorDBFactory.create(config)