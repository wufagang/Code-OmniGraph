import pytest

from cagr_processor.embedding.models import (
    EmbeddingTarget, CollectionName,
    MethodEmbedding, EmbeddingSearchResult, EmbeddingStats,
)


class TestMethodEmbedding:
    """测试 MethodEmbedding 数据模型"""

    def test_required_fields(self):
        e = MethodEmbedding(qualified_name="com.example.Foo#bar", vector=[0.1, 0.2, 0.3])
        assert e.qualified_name == "com.example.Foo#bar"
        assert e.vector == [0.1, 0.2, 0.3]

    def test_optional_fields_default_none(self):
        e = MethodEmbedding(qualified_name="a.B#c", vector=[0.0])
        assert e.name is None
        assert e.signature is None
        assert e.body is None
        assert e.file_path is None
        assert e.class_name is None
        assert e.is_endpoint is False
        assert e.metadata == {}

    def test_full_fields(self):
        e = MethodEmbedding(
            qualified_name="com.example.Foo#bar",
            vector=[0.1, 0.2],
            name="bar",
            signature="void bar(String s)",
            body="public void bar(String s) { }",
            file_path="src/Foo.java",
            class_name="com.example.Foo",
            is_endpoint=True,
            metadata={"custom_key": "value"},
        )
        assert e.name == "bar"
        assert e.is_endpoint is True
        assert e.metadata == {"custom_key": "value"}


class TestEmbeddingSearchResult:
    """测试 EmbeddingSearchResult 模型"""

    def test_required_fields(self):
        r = EmbeddingSearchResult(qualified_name="com.example.Foo#bar", score=0.95)
        assert r.qualified_name == "com.example.Foo#bar"
        assert r.score == pytest.approx(0.95)

    def test_optional_fields_default(self):
        r = EmbeddingSearchResult(qualified_name="a.B#c", score=0.5)
        assert r.name is None
        assert r.body is None
        assert r.is_endpoint is False


class TestEmbeddingStats:
    """测试 EmbeddingStats 模型"""

    def test_defaults(self):
        s = EmbeddingStats(collection_name="code_functions")
        assert s.collection_name == "code_functions"
        assert s.vector_count == 0
        assert s.vector_size is None

    def test_with_values(self):
        s = EmbeddingStats(collection_name="code_functions", vector_count=100, vector_size=768)
        assert s.vector_count == 100
        assert s.vector_size == 768


class TestEnums:
    """测试枚举类型"""

    def test_embedding_target(self):
        assert EmbeddingTarget.FUNCTION == "function"
        assert EmbeddingTarget.CLASS == "class"
        assert EmbeddingTarget.FILE == "file"

    def test_collection_name(self):
        assert CollectionName.FUNCTIONS == "code_functions"
        assert CollectionName.CLASSES == "code_classes"
