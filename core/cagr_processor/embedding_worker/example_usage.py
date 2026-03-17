"""
向量数据库模块使用示例
"""

from embedding_worker import (
    create_vector_db,
    VectorDBConfig,
    QdrantConfig,
    MilvusConfig,
    VectorData,
    SearchParams,
    HybridSearchParams,
    DistanceMetric,
    IndexType
)


def example_qdrant_usage():
    """Qdrant使用示例"""
    print("=== Qdrant 使用示例 ===")

    # 方法1: 使用便捷函数创建
    db = create_vector_db(
        "qdrant",
        host="localhost",
        port=6333,
        url=None  # 或者使用 url="http://localhost:6333"
    )

    # 方法2: 使用配置对象创建
    config = VectorDBConfig(
        db_type="qdrant",
        qdrant_config=QdrantConfig(
            host="localhost",
            port=6333
        )
    )
    # db = VectorDBFactory.create(config)

    # 创建集合
    collection_name = "test_collection"
    db.create_collection(
        collection_name=collection_name,
        vector_size=384,
        distance_metric=DistanceMetric.COSINE,
        index_type=IndexType.HNSW
    )

    # 插入数据
    data = [
        VectorData(id="1", vector=[0.1] * 384, payload={"text": "hello"}),
        VectorData(id="2", vector=[0.2] * 384, payload={"text": "world"}),
        VectorData(id="3", vector=[0.3] * 384, payload={"text": "test"}),
    ]
    inserted_count = db.insert(collection_name, data)
    print(f"插入了 {inserted_count} 条数据")

    # 搜索
    search_params = SearchParams(
        collection_name=collection_name,
        query_vector=[0.15] * 384,
        limit=2
    )
    results = db.search(search_params)
    print(f"搜索结果: {len(results)} 条")
    for result in results:
        print(f"  ID: {result.id}, Score: {result.score}, Payload: {result.payload}")

    # 查询集合信息
    info = db.get_collection_info(collection_name)
    print(f"集合信息: {info}")

    # 关闭连接
    db.close()


def example_milvus_usage():
    """Milvus使用示例"""
    print("\n=== Milvus 使用示例 ===")

    # 创建Milvus实例
    db = create_vector_db(
        "milvus",
        host="localhost",
        port=19530,
        user="root",  # 可选
        password="milvus"  # 可选
    )

    # 创建集合
    collection_name = "test_milvus_collection"
    db.create_collection(
        collection_name=collection_name,
        vector_size=512,
        distance_metric=DistanceMetric.EUCLIDEAN
    )

    # 插入数据
    data = [
        VectorData(id=f"vec_{i}", vector=[i * 0.01] * 512, payload={"index": i})
        for i in range(10)
    ]
    inserted_count = db.insert(collection_name, data, batch_size=5)
    print(f"插入了 {inserted_count} 条数据")

    # 搜索
    results = db.search(SearchParams(
        collection_name=collection_name,
        query_vector=[0.05] * 512,
        limit=3,
        with_vectors=False
    ))
    print(f"搜索结果: {len(results)} 条")
    for result in results:
        print(f"  ID: {result.id}, Score: {result.score}")

    # 删除数据
    deleted_count = db.delete(collection_name, ids=["vec_1", "vec_3"])
    print(f"删除了 {deleted_count} 条数据")

    # 查询数据
    query_results = db.query(
        collection_name=collection_name,
        filter={"index": {"$gte": 5}},
        limit=5
    )
    print(f"查询结果: {len(query_results)} 条")

    # 关闭连接
    db.close()


def example_hybrid_search():
    """混合搜索示例"""
    print("\n=== 混合搜索示例 ===")

    # 创建支持混合向量的数据库
    db = create_vector_db("qdrant")

    # 创建混合向量集合
    collection_name = "hybrid_collection"
    db.create_hybrid_collection(
        collection_name=collection_name,
        dense_vector_size=384,
        sparse_vector_size=10000,  # 稀疏向量的词汇表大小
        distance_metric=DistanceMetric.COSINE
    )

    # 插入混合向量数据
    dense_data = [
        VectorData(id="1", vector=[0.1] * 384),
        VectorData(id="2", vector=[0.2] * 384),
    ]
    sparse_data = [
        VectorData(id="1", vector={"hello": 1.0, "world": 0.5}),
        VectorData(id="2", vector={"foo": 0.8, "bar": 1.0}),
    ]

    db.insert_hybrid(collection_name, dense_data, sparse_data)

    # 执行混合搜索
    results = db.hybrid_search(HybridSearchParams(
        collection_name=collection_name,
        dense_vector=[0.15] * 384,
        sparse_vector={"hello": 0.8, "test": 0.3},
        alpha=0.7,  # 稠密向量权重
        limit=5
    ))
    print(f"混合搜索结果: {len(results)} 条")

    db.close()


def example_batch_operations():
    """批量操作示例"""
    print("\n=== 批量操作示例 ===")

    db = create_vector_db("qdrant")
    collection_name = "batch_collection"

    # 创建集合
    db.create_collection(collection_name, vector_size=256)

    # 批量插入大量数据
    large_data = [
        VectorData(id=f"batch_{i}", vector=[i * 0.001] * 256)
        for i in range(1000)
    ]

    # 使用批量插入，每批100条
    inserted = db.insert(collection_name, large_data, batch_size=100)
    print(f"批量插入了 {inserted} 条数据")

    # 批量删除
    delete_ids = [f"batch_{i}" for i in range(100, 200)]
    deleted = db.delete(collection_name, ids=delete_ids)
    print(f"批量删除了 {deleted} 条数据")

    db.close()


def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")

    from embedding_worker import CollectionNotFoundException, ConfigException

    try:
        # 尝试连接不存在的服务
        db = create_vector_db("qdrant", host="invalid_host", port=9999)
    except ConfigException as e:
        print(f"配置错误: {e}")

    try:
        db = create_vector_db("qdrant")

        # 尝试操作不存在的集合
        db.search(SearchParams(
            collection_name="non_existent_collection",
            query_vector=[0.1] * 100
        ))
    except CollectionNotFoundException as e:
        print(f"集合不存在: {e}")
    except Exception as e:
        print(f"其他错误: {e}")


if __name__ == "__main__":
    # 运行示例
    try:
        example_qdrant_usage()
        # example_milvus_usage()  # 需要安装pymilvus
        # example_hybrid_search()
        # example_batch_operations()
        # example_error_handling()
    except Exception as e:
        print(f"示例运行出错: {e}")
        import traceback
        traceback.print_exc()