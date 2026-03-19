import pytest
from unittest.mock import Mock, MagicMock

from cagr_processor.embedding.embedding_service import EmbeddingService
from cagr_processor.embedding.models import (
    MethodEmbedding, EmbeddingSearchResult, EmbeddingStats, CollectionName,
)
from cagr_processor.embedding_dao.models import (
    VectorData, SearchResult, CollectionInfo, DistanceMetric,
)


def _make_mock_db(has_collection: bool = True) -> Mock:
    """创建标准 Mock VectorDatabase"""
    db = Mock()
    db.has_collection.return_value = has_collection
    db.create_collection.return_value = True
    db.drop_collection.return_value = True
    db.insert.return_value = 1

    mock_info = CollectionInfo(
        name=CollectionName.FUNCTIONS,
        vector_size=768,
        distance_metric=DistanceMetric.COSINE,
        vector_count=42,
    )
    db.get_collection_info.return_value = mock_info

    search_result = SearchResult(
        id="com.example.Foo#bar",
        score=0.95,
        payload={
            "name": "bar",
            "signature": "void bar()",
            "body": "public void bar() {}",
            "file_path": "src/Foo.java",
            "class_name": "com.example.Foo",
            "is_endpoint": True,
        },
    )
    db.search.return_value = [search_result]
    db.delete.return_value = 1
    return db


class TestEnsureCollection:
    """测试 ensure_collection"""

    def test_already_exists_skips_create(self):
        db = _make_mock_db(has_collection=True)
        service = EmbeddingService(db)
        result = service.ensure_collection(vector_size=768)
        assert result is True
        db.create_collection.assert_not_called()

    def test_not_exists_creates(self):
        db = _make_mock_db(has_collection=False)
        service = EmbeddingService(db)
        result = service.ensure_collection(vector_size=768)
        assert result is True
        db.create_collection.assert_called_once_with(
            collection_name=CollectionName.FUNCTIONS,
            vector_size=768,
            distance_metric=DistanceMetric.COSINE,
        )

    def test_custom_distance_metric(self):
        db = _make_mock_db(has_collection=False)
        service = EmbeddingService(db)
        service.ensure_collection(vector_size=512, distance_metric=DistanceMetric.DOT_PRODUCT)
        _, kwargs = db.create_collection.call_args
        assert kwargs["distance_metric"] == DistanceMetric.DOT_PRODUCT


class TestDropCollection:
    """测试 drop_collection"""

    def test_drop(self):
        db = _make_mock_db()
        service = EmbeddingService(db)
        assert service.drop_collection() is True
        db.drop_collection.assert_called_once_with(CollectionName.FUNCTIONS)


class TestUpsertMethods:
    """测试 upsert_method / upsert_methods"""

    def test_upsert_single(self):
        db = _make_mock_db()
        db.insert.return_value = 1
        service = EmbeddingService(db)

        embedding = MethodEmbedding(
            qualified_name="com.example.Foo#bar",
            vector=[0.1, 0.2, 0.3],
            name="bar",
            body="public void bar() {}",
            is_endpoint=True,
        )
        count = service.upsert_method(embedding)
        assert count == 1
        db.insert.assert_called_once()

        # 校验传入的 VectorData
        call_args = db.insert.call_args
        collection, data = call_args[0]
        assert collection == CollectionName.FUNCTIONS
        assert len(data) == 1
        assert data[0].id == "com.example.Foo#bar"
        assert data[0].vector == [0.1, 0.2, 0.3]
        assert data[0].payload["name"] == "bar"
        assert data[0].payload["is_endpoint"] is True

    def test_upsert_batch(self):
        db = _make_mock_db()
        db.insert.return_value = 3
        service = EmbeddingService(db)

        embeddings = [
            MethodEmbedding(qualified_name=f"com.A#m{i}", vector=[float(i)] * 4)
            for i in range(3)
        ]
        count = service.upsert_methods(embeddings)
        assert count == 3
        _, data = db.insert.call_args[0]
        assert len(data) == 3

    def test_payload_excludes_none_fields(self):
        db = _make_mock_db()
        service = EmbeddingService(db)

        embedding = MethodEmbedding(qualified_name="a.B#c", vector=[0.1])
        service.upsert_method(embedding)

        _, data = db.insert.call_args[0]
        vd: VectorData = data[0]
        # name/body 等为 None，不应出现在 payload 中
        assert vd.payload is None or "name" not in (vd.payload or {})

    def test_metadata_merged_into_payload(self):
        db = _make_mock_db()
        service = EmbeddingService(db)

        embedding = MethodEmbedding(
            qualified_name="a.B#c",
            vector=[0.1],
            metadata={"custom": "data"},
        )
        service.upsert_method(embedding)
        _, data = db.insert.call_args[0]
        assert data[0].payload["custom"] == "data"


class TestDeleteMethod:
    """测试 delete_method"""

    def test_delete_by_qualified_name(self):
        db = _make_mock_db()
        service = EmbeddingService(db)

        count = service.delete_method("com.example.Foo#bar")
        assert count == 1
        db.delete.assert_called_once_with(
            CollectionName.FUNCTIONS, ids=["com.example.Foo#bar"]
        )


class TestSearchSimilarMethods:
    """测试 search_similar_methods"""

    def test_returns_search_results(self):
        db = _make_mock_db()
        service = EmbeddingService(db)

        results = service.search_similar_methods(query_vector=[0.1, 0.2], limit=5)
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, EmbeddingSearchResult)
        assert r.qualified_name == "com.example.Foo#bar"
        assert r.score == pytest.approx(0.95)
        assert r.name == "bar"
        assert r.body == "public void bar() {}"
        assert r.is_endpoint is True

    def test_search_params_forwarded(self):
        db = _make_mock_db()
        service = EmbeddingService(db)

        service.search_similar_methods(
            query_vector=[0.1, 0.2],
            limit=3,
            score_threshold=0.8,
            filter={"is_endpoint": True},
        )
        call_args = db.search.call_args[0][0]
        assert call_args.limit == 3
        assert call_args.score_threshold == pytest.approx(0.8)
        assert call_args.filter == {"is_endpoint": True}

    def test_empty_payload_handled(self):
        db = _make_mock_db()
        db.search.return_value = [SearchResult(id="a.B#c", score=0.7, payload=None)]
        service = EmbeddingService(db)

        results = service.search_similar_methods(query_vector=[0.1])
        assert results[0].name is None
        assert results[0].is_endpoint is False


class TestGetStats:
    """测试 get_stats"""

    def test_stats_mapped_correctly(self):
        db = _make_mock_db()
        service = EmbeddingService(db)

        stats = service.get_stats()
        assert isinstance(stats, EmbeddingStats)
        assert stats.collection_name == CollectionName.FUNCTIONS
        assert stats.vector_count == 42
        assert stats.vector_size == 768

    def test_custom_collection_name(self):
        db = _make_mock_db()
        mock_info = CollectionInfo(
            name="custom_col",
            vector_size=512,
            distance_metric=DistanceMetric.COSINE,
            vector_count=0,
        )
        db.get_collection_info.return_value = mock_info
        service = EmbeddingService(db, collection_name="custom_col")

        stats = service.get_stats()
        assert stats.collection_name == "custom_col"
        assert stats.vector_size == 512
