import pytest
from unittest.mock import Mock, patch

from cagr_processor.embedding_worker.base import BaseVectorDatabase, retry_on_failure
from cagr_processor.embedding_worker.models import VectorData, DistanceMetric, IndexType
from cagr_common.exceptions import (
    VectorConnectionException, VectorCollectionNotFoundException,
    VectorCollectionAlreadyExistsException, VectorInsertException
)


class MockBaseVectorDatabase(BaseVectorDatabase):
    """用于测试的基础类实现"""

    def __init__(self, config=None):
        super().__init__(config or Mock())
        self._connection = True  # 模拟已连接

    def _create_collection_impl(self, *args, **kwargs):
        return True

    def _create_hybrid_collection_impl(self, *args, **kwargs):
        return True

    def _insert_impl(self, collection_name, data):
        return len(data)

    def _search_impl(self, params):
        return []

    def _delete_impl(self, collection_name, ids, filter):
        return len(ids) if ids else 1

    def drop_collection(self, collection_name):
        return True

    def has_collection(self, collection_name):
        return collection_name != "non_existent"

    def list_collections(self):
        return ["collection1", "collection2"]

    def get_collection_info(self, collection_name):
        from cagr_processor.embedding_worker.models import CollectionInfo
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

    def check_collection_limit(self, collection_name):
        from cagr_processor.embedding_worker.models import CollectionLimit
        return CollectionLimit()

    def close(self):
        self._connection = False


class TestRetryDecorator:
    """测试重试装饰器"""

    def test_retry_success_on_first_attempt(self):
        """测试第一次尝试就成功"""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.01)
        def success_function(self):
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_function(None)
        assert result == "success"
        assert call_count == 1

    def test_retry_success_after_failures(self):
        """测试失败后重试成功"""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.01)
        def fail_then_succeed(self):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise VectorConnectionException("Connection failed")
            return "success"

        result = fail_then_succeed(None)
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted(self):
        """测试重试次数耗尽"""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.01)
        def always_fail(self):
            nonlocal call_count
            call_count += 1
            raise VectorConnectionException("Always fails")

        with pytest.raises(VectorConnectionException):
            always_fail(None)

        assert call_count == 3

    def test_retry_non_connection_exception(self):
        """测试非连接异常不重试"""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.01)
        def fail_with_other_exception(self):
            nonlocal call_count
            call_count += 1
            raise ValueError("Other error")

        with pytest.raises(ValueError):
            fail_with_other_exception(None)

        assert call_count == 1  # 不重试


class TestBaseVectorDatabase:
    """测试基础向量数据库类"""

    def setup_method(self):
        """测试前准备"""
        self.config = Mock()
        self.config.enable_logging = True
        self.db = MockBaseVectorDatabase(self.config)

    def test_validate_connection(self):
        """测试连接验证"""
        self.db._validate_connection()  # 应该不抛出异常

        self.db._connection = None
        with pytest.raises(VectorConnectionException):
            self.db._validate_connection()

    def test_validate_collection_name(self):
        """测试集合名称验证"""
        # 有效名称
        self.db._validate_collection_name("valid_name")
        self.db._validate_collection_name("collection_123")

        # 无效名称
        with pytest.raises(ValueError):
            self.db._validate_collection_name("")

        with pytest.raises(ValueError):
            self.db._validate_collection_name(None)

        with pytest.raises(ValueError):
            self.db._validate_collection_name("a" * 256)  # 太长

    def test_validate_vector_data(self):
        """测试向量数据验证"""
        # 有效数据
        valid_data = [
            VectorData(id="1", vector=[0.1, 0.2, 0.3]),
            VectorData(id="2", vector=[0.4, 0.5, 0.6])
        ]
        self.db._validate_vector_data(valid_data)

        # 空数据
        with pytest.raises(ValueError):
            self.db._validate_vector_data([])

        # 不一致的向量维度
        inconsistent_data = [
            VectorData(id="1", vector=[0.1, 0.2]),
            VectorData(id="2", vector=[0.3, 0.4, 0.5])  # 不同维度
        ]
        with pytest.raises(ValueError):
            self.db._validate_vector_data(inconsistent_data)

    def test_batch_operation(self):
        """测试批量操作"""
        items = list(range(10))
        batch_size = 3
        results = []

        def operation(batch):
            results.extend(batch)
            return len(batch)

        total = self.db._batch_operation(items, batch_size, operation)

        assert total == 10
        assert results == list(range(10))

    def test_update_collection_cache(self):
        """测试更新集合缓存"""
        from cagr_processor.embedding_worker.models import CollectionInfo, DistanceMetric

        info = CollectionInfo(
            name="test_collection",
            vector_size=768,
            distance_metric=DistanceMetric.COSINE
        )

        self.db._update_collection_cache("test_collection", info)
        cached = self.db._get_from_cache("test_collection")

        assert cached == info

    def test_clear_collection_cache(self):
        """测试清除集合缓存"""
        from cagr_processor.embedding_worker.models import CollectionInfo, DistanceMetric

        info = CollectionInfo(
            name="test_collection",
            vector_size=768,
            distance_metric=DistanceMetric.COSINE
        )

        self.db._update_collection_cache("test_collection", info)
        self.db._clear_collection_cache("test_collection")
        cached = self.db._get_from_cache("test_collection")

        assert cached is None

    def test_insert_with_batching(self):
        """测试带批次的插入"""
        # 创建大量数据
        large_data = [
            VectorData(id=f"item_{i}", vector=[i * 0.1] * 10)
            for i in range(25)
        ]

        # 设置较小的批次大小
        self.config.default_batch_size = 10

        # 插入数据
        count = self.db.insert("test_collection", large_data)

        assert count == 25

    def test_insert_collection_not_found(self):
        """测试插入到不存在的集合"""
        data = [VectorData(id="1", vector=[0.1, 0.2])]

        with pytest.raises(VectorCollectionNotFoundException):
            self.db.insert("non_existent", data)

    def test_delete_validation(self):
        """测试删除验证"""
        # 不提供ids或filter
        with pytest.raises(ValueError):
            self.db.delete("test_collection")

        # 提供ids
        result = self.db.delete("test_collection", ids=["1", "2", "3"])
        assert result == 3

        # 提供filter
        result = self.db.delete("test_collection", filter={"status": "old"})
        assert result == 1

    def test_retry_on_connection(self):
        """测试连接重试"""
        # 模拟连接失败
        call_count = 0

        def mock_insert(self, collection_name, data):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise VectorConnectionException("Connection failed")
            return len(data)

        # 替换方法
        self.db._insert_impl = mock_insert.__get__(self.db)

        data = [VectorData(id="1", vector=[0.1, 0.2])]
        result = self.db.insert("test_collection", data)

        assert result == 1
        assert call_count == 3

    def test_logging_disabled(self):
        """测试禁用日志"""
        self.config.enable_logging = False

        # 应该不记录日志，这里只是测试不抛出异常
        data = [VectorData(id="1", vector=[0.1, 0.2])]
        self.db.insert("test_collection", data)

        # 如果日志被正确禁用，应该不会出错