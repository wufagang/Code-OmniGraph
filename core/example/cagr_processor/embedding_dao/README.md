# Code-OmniGraph 向量数据库模块（embedding_dao）

## 模块架构

```
调用方
       ↓
VectorDatabase 接口        # cagr_processor.embedding_dao.interfaces
  职责：统一向量数据库操作契约
       ↓
BaseVectorDatabase         # cagr_processor.embedding_dao.base
  职责：重试机制、参数验证、批量操作、集合缓存等基础设施
       ↓
QdrantDatabase / MilvusDatabase   # cagr_processor.embedding_dao.impl.*
  职责：具体数据库驱动实现
```

领域模型定义在 `cagr_processor.embedding_dao.models`，配置定义在 `cagr_processor.embedding_dao.config`。

---

## 前提条件

**1. 启动向量数据库（Docker）**

Qdrant：
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  qdrant/qdrant
```

Milvus（参考 [官方文档](https://milvus.io/docs/install_standalone-docker.md)）：
```bash
docker run -d \
  --name milvus \
  -p 19530:19530 \
  milvusdb/milvus:latest
```

**2. 安装 Python 依赖**
```bash
pip install -r core/requirements.txt

# 或按需单独安装
pip install qdrant-client    # 使用 Qdrant 时
pip install pymilvus         # 使用 Milvus 时
```

**3. 配置环境变量**
```bash
# Qdrant（默认）
export VECTOR_DB_TYPE=qdrant
export QDRANT_HOST=localhost
export QDRANT_PORT=6333

# Milvus
export VECTOR_DB_TYPE=milvus
export MILVUS_HOST=localhost
export MILVUS_PORT=19530
```

---

## 快速开始

### 使用便捷函数

```python
from cagr_processor.embedding_dao import create_vector_db, VectorData, SearchParams

# 从环境变量创建（无参数）
db = create_vector_db()

# 直接指定参数（Qdrant）
db = create_vector_db("qdrant", host="localhost", port=6333)

# 直接指定参数（Milvus）
db = create_vector_db("milvus", host="localhost", port=19530)
```

### 基本操作流程

```python
from cagr_processor.embedding_dao import (
    create_vector_db, VectorData, SearchParams, DistanceMetric
)

db = create_vector_db("qdrant", host="localhost", port=6333)

try:
    # 1. 创建集合
    db.create_collection(
        collection_name="code_methods",
        vector_size=768,
        distance_metric=DistanceMetric.COSINE
    )

    # 2. 插入向量数据
    data = [
        VectorData(id="method_1", vector=[0.1] * 768, payload={"name": "getUserById", "class": "UserService"}),
        VectorData(id="method_2", vector=[0.2] * 768, payload={"name": "createUser", "class": "UserService"}),
    ]
    count = db.insert("code_methods", data)
    print(f"插入 {count} 条记录")

    # 3. 向量搜索
    results = db.search(SearchParams(
        collection_name="code_methods",
        query_vector=[0.15] * 768,
        limit=5,
        score_threshold=0.7
    ))
    for r in results:
        print(f"  {r.id}  score={r.score:.4f}  {r.payload}")

    # 4. 获取集合信息
    info = db.get_collection_info("code_methods")
    print(f"向量数量: {info.vector_count}，维度: {info.vector_size}")

finally:
    db.close()
```

---

## 配置

### 使用配置对象

```python
from cagr_processor.embedding_dao import VectorDBConfig, QdrantConfig, MilvusConfig, VectorDBFactory

# Qdrant
config = VectorDBConfig(
    db_type="qdrant",
    qdrant_config=QdrantConfig(
        host="localhost",
        port=6333,
        api_key="your-api-key",   # 可选，云端部署时使用
        prefer_grpc=False,
        timeout=30.0
    ),
    max_connections=10,
    retry_attempts=3,
)
db = VectorDBFactory.create(config)

# Milvus
config = VectorDBConfig(
    db_type="milvus",
    milvus_config=MilvusConfig(
        host="localhost",
        port=19530,
        user="root",
        password="milvus",
        db_name="default",
        secure=False
    )
)
db = VectorDBFactory.create(config)

# 从环境变量创建
db = VectorDBFactory.create_from_env()
```

### 环境变量参考

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VECTOR_DB_TYPE` | 数据库类型（`qdrant` / `milvus`） | `qdrant` |
| `QDRANT_HOST` | Qdrant 主机 | `localhost` |
| `QDRANT_PORT` | Qdrant 端口 | `6333` |
| `QDRANT_URL` | Qdrant 完整 URL（优先于 host:port） | - |
| `QDRANT_API_KEY` | Qdrant API 密钥（云端认证） | - |
| `QDRANT_PREFER_GRPC` | 使用 gRPC 协议 | `false` |
| `QDRANT_TIMEOUT` | 请求超时（秒） | `30.0` |
| `MILVUS_HOST` | Milvus 主机 | `localhost` |
| `MILVUS_PORT` | Milvus 端口 | `19530` |
| `MILVUS_URI` | Milvus URI（优先于 host:port） | - |
| `MILVUS_USER` | Milvus 用户名 | - |
| `MILVUS_PASSWORD` | Milvus 密码 | - |
| `MILVUS_DB_NAME` | Milvus 数据库名 | `default` |
| `MILVUS_SECURE` | 使用 TLS 连接 | `false` |

---

## 接口方法

### 集合管理

```python
# 创建普通集合
db.create_collection("my_collection", vector_size=768, distance_metric=DistanceMetric.COSINE)

# 创建混合向量集合（稠密 + 稀疏）
db.create_hybrid_collection(
    collection_name="hybrid_collection",
    dense_vector_size=768,
    sparse_vector_size=10000,  # 词汇表大小
    distance_metric=DistanceMetric.COSINE
)

db.has_collection("my_collection")        # 检查集合是否存在 → bool
db.list_collections()                      # 列出所有集合 → List[str]
db.get_collection_info("my_collection")   # 获取集合信息 → CollectionInfo
db.check_collection_limit("my_collection") # 检查容量限制 → CollectionLimit
db.drop_collection("my_collection")       # 删除集合 → bool
```

### 数据写入

```python
# 普通插入（自动分批，默认 batch_size=100）
db.insert("my_collection", data, batch_size=500)

# 混合向量插入
dense_data  = [VectorData(id="1", vector=[0.1] * 768)]
sparse_data = [VectorData(id="1", vector={"hello": 1.0, "world": 0.5})]
db.insert_hybrid("hybrid_collection", dense_data, sparse_data)

# 删除（按 id 或 filter）
db.delete("my_collection", ids=["id_1", "id_2"])
db.delete("my_collection", filter={"category": "deprecated"})
```

### 搜索与查询

```python
from cagr_processor.embedding_dao import SearchParams, HybridSearchParams

# 普通向量搜索
results = db.search(SearchParams(
    collection_name="my_collection",
    query_vector=[0.1] * 768,
    limit=10,
    score_threshold=0.7,
    filter={"language": "java"},
    with_vectors=False
))

# 混合搜索（稠密 + 稀疏）
results = db.hybrid_search(HybridSearchParams(
    collection_name="hybrid_collection",
    dense_vector=[0.1] * 768,
    sparse_vector={"getUserById": 0.9, "service": 0.4},
    alpha=0.7,          # 稠密向量权重（1-alpha 为稀疏权重）
    limit=10,
))

# 按条件查询（不依赖向量相似度）
items = db.query(
    collection_name="my_collection",
    filter={"class": "UserService"},
    limit=20,
    with_vectors=True
)
```

---

## 数据模型

| 类 | 说明 |
|----|------|
| `VectorData` | 向量数据：`id`、`vector`、`payload` |
| `SearchResult` | 搜索结果：`id`、`score`、`vector`、`payload` |
| `CollectionInfo` | 集合元信息：名称、维度、距离类型、向量数量 |
| `CollectionLimit` | 集合容量限制信息 |
| `SearchParams` | 普通搜索参数 |
| `HybridSearchParams` | 混合搜索参数（`alpha` 控制权重） |
| `DistanceMetric` | 距离类型枚举：`COSINE` / `EUCLIDEAN` / `DOT_PRODUCT` / `HAMMING` |
| `IndexType` | 索引类型枚举：`FLAT` / `HNSW` / `IVF_FLAT` 等 |

---

## 错误处理

```python
from cagr_processor.embedding_dao import (
    VectorDBException,
    VectorConnectionException,
    VectorCollectionNotFoundException,
    VectorCollectionAlreadyExistsException,
    VectorInsertException,
    VectorSearchException,
    VectorConfigException,
)

try:
    results = db.search(SearchParams(
        collection_name="nonexistent",
        query_vector=[0.1] * 768
    ))
except VectorCollectionNotFoundException as e:
    print(f"集合不存在: {e}")
except VectorConnectionException as e:
    print(f"连接失败: {e}")
except VectorSearchException as e:
    print(f"搜索错误: {e}")
except VectorDBException as e:
    print(f"向量数据库通用错误: {e}")
```

内置重试机制：连接异常（`VectorConnectionException`）会自动重试，默认最多 3 次、间隔 1 秒。

---

## 扩展新数据库

```python
from cagr_processor.embedding_dao.base import BaseVectorDatabase
from cagr_processor.embedding_dao.factory import VectorDBFactory

class MyVectorDB(BaseVectorDatabase):
    def _create_collection_impl(self, collection_name, vector_size, distance_metric, index_type, **kwargs):
        # 实现创建集合逻辑
        ...

    def _insert_impl(self, collection_name, data):
        # 实现插入逻辑
        ...

    def _search_impl(self, params):
        # 实现搜索逻辑
        ...

    def _delete_impl(self, collection_name, ids, filter):
        # 实现删除逻辑
        ...

    # 还需实现：_create_hybrid_collection_impl、以及接口中的其他方法

# 注册到工厂
VectorDBFactory.register("my_db", MyVectorDB)

# 使用
db = create_vector_db("my_db", host="...")
```

---

## 常见问题

**连接失败**
```bash
docker ps              # 确认数据库容器运行中
docker logs qdrant     # 查看 Qdrant 日志
docker logs milvus     # 查看 Milvus 日志
```

**ModuleNotFoundError**
```bash
pip install qdrant-client   # Qdrant 驱动
pip install pymilvus        # Milvus 驱动
```

**插入时集合不存在**
`insert()` 会在集合不存在时抛出 `VectorCollectionNotFoundException`，需先调用 `create_collection()` 或 `has_collection()` 检查。

**批量插入性能调优**
- 调整 `batch_size` 参数（默认 100），较大数据集建议 500~1000
- Qdrant 可启用 `prefer_grpc=True` 提升吞吐量
- 避免频繁断连，保持连接复用
