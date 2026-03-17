# 向量数据库模块

这个模块提供了一个统一的接口来支持多种向量数据库，包括 Qdrant 和 Milvus。

## 特性

- 🔧 **多数据库支持**: 支持 Qdrant 和 Milvus 向量数据库
- 🎯 **统一接口**: 所有数据库都实现相同的 VectorDatabase 接口
- 🔌 **易于扩展**: 通过工厂模式轻松添加新的数据库支持
- 🚀 **高性能**: 支持批量操作和连接池
- 🛡️ **健壮性**: 完善的错误处理和重试机制
- 🔍 **混合搜索**: 支持稠密向量和稀疏向量的混合搜索
- ⚙️ **灵活配置**: 支持代码配置、环境变量和配置文件

## 快速开始

### 基本使用

```python
from embedding_worker import create_vector_db, VectorData, SearchParams

# 创建数据库实例
db = create_vector_db("qdrant", host="localhost", port=6333)

# 创建集合
db.create_collection("my_collection", vector_size=768)

# 插入数据
data = [
    VectorData(id="1", vector=[0.1] * 768, payload={"text": "hello"}),
    VectorData(id="2", vector=[0.2] * 768, payload={"text": "world"}),
]
db.insert("my_collection", data)

# 搜索
results = db.search(SearchParams(
    collection_name="my_collection",
    query_vector=[0.15] * 768,
    limit=5
))

# 关闭连接
db.close()
```

### 使用环境变量

```bash
# 设置环境变量
export VECTOR_DB_TYPE=qdrant
export QDRANT_HOST=localhost
export QDRANT_PORT=6333

# 在代码中使用
db = create_vector_db()  # 无参数，从环境变量加载
```

## 配置选项

### Qdrant 配置

```python
from embedding_worker import VectorDBConfig, QdrantConfig

config = VectorDBConfig(
    db_type="qdrant",
    qdrant_config=QdrantConfig(
        host="localhost",
        port=6333,
        url="http://localhost:6333",  # 或者使用URL
        api_key="your-api-key",       # 如果需要认证
        prefer_grpc=False,
        timeout=30.0
    ),
    max_connections=10,
    retry_attempts=3,
    enable_logging=True
)
```

### Milvus 配置

```python
from embedding_worker import VectorDBConfig, MilvusConfig

config = VectorDBConfig(
    db_type="milvus",
    milvus_config=MilvusConfig(
        host="localhost",
        port=19530,
        uri="http://localhost:19530",  # 或者使用URI
        user="root",
        password="milvus",
        db_name="default",
        secure=False
    )
)
```

## 高级功能

### 混合向量搜索

支持同时搜索稠密向量和稀疏向量：

```python
# 创建混合向量集合
db.create_hybrid_collection(
    collection_name="hybrid_collection",
    dense_vector_size=768,
    sparse_vector_size=10000,  # 词汇表大小
    distance_metric="cosine"
)

# 插入混合数据
dense_data = [VectorData(id="1", vector=[0.1] * 768)]
sparse_data = [VectorData(id="1", vector={"hello": 1.0, "world": 0.5})]
db.insert_hybrid("hybrid_collection", dense_data, sparse_data)

# 混合搜索
results = db.hybrid_search(HybridSearchParams(
    collection_name="hybrid_collection",
    dense_vector=[0.1] * 768,
    sparse_vector={"hello": 0.8, "test": 0.3},
    alpha=0.7,  # 稠密向量权重
    limit=5
))
```

### 批量操作

```python
# 批量插入大量数据
large_dataset = [VectorData(id=f"item_{i}", vector=[...]) for i in range(10000)]
db.insert("large_collection", large_dataset, batch_size=1000)

# 批量删除
db.delete("large_collection", ids=["item_1", "item_2", "item_3"])
```

### 查询和过滤

```python
# 查询数据
results = db.query(
    collection_name="my_collection",
    filter={"category": "electronics", "price": {"$gte": 100}},
    limit=10,
    with_vectors=True
)

# 获取集合信息
info = db.get_collection_info("my_collection")
print(f"向量数量: {info.vector_count}")
print(f"向量维度: {info.vector_size}")
```

## 错误处理

```python
from embedding_worker import (
    VectorDBException,
    CollectionNotFoundException,
    ConnectionException,
    SearchException
)

try:
    results = db.search(SearchParams(
        collection_name="non_existent",
        query_vector=[0.1] * 100
    ))
except CollectionNotFoundException as e:
    print(f"集合不存在: {e.collection_name}")
except ConnectionException as e:
    print(f"连接错误: {e}")
except VectorDBException as e:
    print(f"向量数据库错误: {e}")
```

## 向后兼容性

为了保持与旧代码的兼容性，提供了 `QdrantWorker` 适配器：

```python
from embedding_worker.qdrant_adapter import QdrantWorker

# 与旧接口相同
worker = QdrantWorker(url="http://localhost:6333")
methods = [...]  # Method对象列表
worker.embed_and_upsert(methods)
```

## 扩展支持

要添加新的向量数据库支持：

1. 创建新的实现类，继承自 `BaseVectorDatabase`
2. 实现所有抽象方法
3. 注册到工厂类

```python
from embedding_worker.base import BaseVectorDatabase

class NewVectorDB(BaseVectorDatabase):
    def _create_collection_impl(self, ...):
        # 实现创建集合逻辑
        pass

    def _insert_impl(self, ...):
        # 实现插入逻辑
        pass

    # 实现其他必需方法...

# 注册到工厂
from embedding_worker.factory import VectorDBFactory
VectorDBFactory.register("new_db", NewVectorDB)
```

## 性能优化建议

1. **批量操作**: 尽量使用批量插入/删除，减少网络往返
2. **连接复用**: 保持数据库连接，避免频繁连接/断开
3. **合理批次大小**: 根据数据大小和网络状况调整批次大小
4. **索引选择**: 根据数据特点选择合适的索引类型
5. **向量维度**: 使用合适的向量维度，避免过高或过低

## 环境变量参考

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| VECTOR_DB_TYPE | 数据库类型 | qdrant |
| QDRANT_HOST | Qdrant主机 | localhost |
| QDRANT_PORT | Qdrant端口 | 6333 |
| QDRANT_URL | Qdrant完整URL | - |
| QDRANT_API_KEY | Qdrant API密钥 | - |
| MILVUS_HOST | Milvus主机 | localhost |
| MILVUS_PORT | Milvus端口 | 19530 |
| MILVUS_URI | Milvus URI | - |
| MILVUS_USER | Milvus用户名 | - |
| MILVUS_PASSWORD | Milvus密码 | - |
| MILVUS_DB_NAME | Milvus数据库名 | default |

## 示例代码

查看 `example_usage.py` 和 `migration_demo.py` 获取完整的使用示例。