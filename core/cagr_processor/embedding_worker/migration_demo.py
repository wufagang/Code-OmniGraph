"""
迁移演示：从旧的QdrantWorker到新的向量数据库模块
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from cagr_common.models import Method

# 旧的实现（qdrant_client.py）
# from embedding_worker.qdrant_client import QdrantWorker

# 新的实现 - 适配器模式
from embedding_worker.qdrant_adapter import QdrantWorker

# 或者使用新的接口直接
from embedding_worker import create_vector_db, VectorData, SearchParams


def demo_old_way():
    """演示旧的用法"""
    print("=== 旧的用法（通过适配器）===")

    # 创建worker（与旧接口相同）
    worker = QdrantWorker(url="http://localhost:6333")

    # 创建测试数据
    methods = [
        Method(id="method1", name="calculateSum", class_name="MathUtils"),
        Method(id="method2", name="validateInput", class_name="Validator"),
        Method(id="method3", name="processData", class_name="DataProcessor"),
    ]

    # 使用旧的接口插入数据
    worker.embed_and_upsert(methods)
    print("使用旧接口插入了3个方法")

    # 适配器会自动关闭连接


def demo_new_way():
    """演示新的用法"""
    print("\n=== 新的用法（直接使用新接口）===")

    # 创建数据库实例
    db = create_vector_db(
        "qdrant",
        host="localhost",
        port=6333
    )

    # 创建集合
    collection_name = "code_methods"
    db.create_collection(
        collection_name=collection_name,
        vector_size=768,  # 假设使用768维向量
        distance_metric="cosine"
    )

    # 准备数据（需要转换格式）
    methods = [
        Method(id="new_method1", name="calculateSum", class_name="MathUtils"),
        Method(id="new_method2", name="validateInput", class_name="Validator"),
        Method(id="new_method3", name="processData", class_name="DataProcessor"),
    ]

    # 转换为新的数据格式
    vector_data = []
    for i, method in enumerate(methods):
        # 这里应该使用真实的嵌入向量，现在用虚拟数据代替
        dummy_vector = [0.1] * 768
        vector_data.append(VectorData(
            id=method.id,
            vector=dummy_vector,
            payload={
                "name": method.name,
                "class_name": method.class_name,
                "type": "method"
            }
        ))

    # 插入数据
    inserted_count = db.insert(collection_name, vector_data)
    print(f"使用新接口插入了 {inserted_count} 个方法")

    # 执行搜索
    # 搜索相似的方法
    query_vector = [0.15] * 768  # 应该使用真实的查询向量
    results = db.search(SearchParams(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=5
    ))

    print(f"搜索到 {len(results)} 个相似方法:")
    for result in results:
        print(f"  - ID: {result.id}, Score: {result.score}")
        if result.payload:
            print(f"    Name: {result.payload.get('name')}")
            print(f"    Class: {result.payload.get('class_name')}")

    # 关闭连接
    db.close()


def demo_advanced_features():
    """演示高级功能"""
    print("\n=== 高级功能演示 ===")

    # 创建数据库
    db = create_vector_db("qdrant")

    # 创建混合向量集合（支持稠密和稀疏向量）
    hybrid_collection = "code_hybrid"
    db.create_hybrid_collection(
        collection_name=hybrid_collection,
        dense_vector_size=768,
        sparse_vector_size=10000,  # 词汇表大小
        distance_metric="cosine"
    )

    # 插入混合数据
    # 稠密向量（语义嵌入）
    dense_data = [
        VectorData(id="code1", vector=[0.1] * 768),
        VectorData(id="code2", vector=[0.2] * 768),
    ]

    # 稀疏向量（TF-IDF或词袋）
    sparse_data = [
        VectorData(id="code1", vector={"function": 1.0, "calculate": 0.8, "math": 0.5}),
        VectorData(id="code2", vector={"class": 1.0, "validator": 0.9, "check": 0.7}),
    ]

    db.insert_hybrid(hybrid_collection, dense_data, sparse_data)
    print("插入了混合向量数据")

    # 执行混合搜索
    results = db.hybrid_search(HybridSearchParams(
        collection_name=hybrid_collection,
        dense_vector=[0.15] * 768,
        sparse_vector={"function": 0.9, "validate": 0.6},
        alpha=0.7,  # 70%权重给稠密向量
        limit=3
    ))
    print(f"混合搜索找到 {len(results)} 个结果")

    # 批量操作
    batch_collection = "batch_test"
    db.create_collection(batch_collection, vector_size=256)

    # 生成大量数据
    large_dataset = []
    for i in range(1000):
        large_dataset.append(VectorData(
            id=f"batch_{i}",
            vector=[i * 0.001] * 256,
            payload={"index": i, "type": "batch_test"}
        ))

    # 批量插入
    batch_size = 100
    inserted = db.insert(batch_collection, large_dataset, batch_size=batch_size)
    print(f"批量插入了 {inserted} 条数据（批次大小: {batch_size}）")

    # 批量删除
    ids_to_delete = [f"batch_{i}" for i in range(100, 200)]
    deleted = db.delete(batch_collection, ids=ids_to_delete)
    print(f"批量删除了 {deleted} 条数据")

    # 查询数据
    query_results = db.query(
        collection_name=batch_collection,
        filter={"type": "batch_test", "index": {"$gte": 500}},
        limit=10
    )
    print(f"查询到 {len(query_results)} 条符合条件的数据")

    # 列出所有集合
    collections = db.list_collections()
    print(f"数据库中的集合: {collections}")

    # 检查集合限制
    for collection in collections[:3]:  # 只检查前3个
        limit_info = db.check_collection_limit(collection)
        print(f"集合 '{collection}' 的向量数量: {limit_info.current_vectors}")

    db.close()


def demo_configuration_options():
    """演示配置选项"""
    print("\n=== 配置选项演示 ===")

    # 1. 环境变量配置
    print("1. 从环境变量加载配置:")
    print("   export VECTOR_DB_TYPE=qdrant")
    print("   export QDRANT_HOST=localhost")
    print("   export QDRANT_PORT=6333")
    # db = create_vector_db()  # 无参数，从环境变量加载

    # 2. 代码配置
    print("\n2. 代码中配置:")
    from embedding_worker import VectorDBConfig, QdrantConfig

    config = VectorDBConfig(
        db_type="qdrant",
        qdrant_config=QdrantConfig(
            host="localhost",
            port=6333,
            api_key="your-api-key",  # 如果需要
            prefer_grpc=False,
            timeout=30.0
        ),
        max_connections=20,
        retry_attempts=5,
        enable_logging=True
    )
    print("   创建了自定义配置")

    # 3. 字典配置
    print("\n3. 字典配置:")
    config_dict = {
        "db_type": "milvus",
        "milvus_config": {
            "host": "localhost",
            "port": 19530,
            "user": "root",
            "password": "milvus"
        },
        "max_connections": 10,
        "retry_attempts": 3
    }
    # db = VectorDBFactory.create_from_config_dict(config_dict)
    print("   从字典创建了配置")


if __name__ == "__main__":
    print("向量数据库模块迁移演示")
    print("=" * 50)

    try:
        # 运行演示
        demo_old_way()
        demo_new_way()
        demo_advanced_features()
        demo_configuration_options()

        print("\n" + "=" * 50)
        print("迁移演示完成!")
        print("\n主要变化:")
        print("1. 从单一Qdrant支持扩展到多数据库支持")
        print("2. 更清晰的接口设计和类型提示")
        print("3. 更灵活的配置管理")
        print("4. 支持混合向量搜索")
        print("5. 更好的错误处理和重试机制")
        print("6. 批量操作和性能优化")

    except Exception as e:
        print(f"演示出错: {e}")
        import traceback
        traceback.print_exc()