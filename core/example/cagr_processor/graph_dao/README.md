# Code-OmniGraph Neo4j 图数据库使用示例

## 模块架构

本示例基于以下三层架构：

```
调用方（示例代码）
       ↓
CodeGraphService          # cagr_processor.graph_code.graph_service
  职责：领域模型字段映射、业务决策、查询结果组装
       ↓
GraphDatabase 接口        # cagr_processor.graph_dao.interfaces
  职责：通用 DB 操作契约（create_node / execute_cypher 等）
       ↓
Neo4jDatabase             # cagr_processor.graph_dao.impl.neo4j_impl
  职责：Cypher 执行，不含业务语义
```

领域模型定义在 `cagr_processor.graph_code.models`，包括节点类型、关系类型和枚举。

---

## 前提条件

**1. 启动 Neo4j（Docker）**
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

**2. 安装 Python 依赖**
```bash
pip install -r core/requirements.txt
```

**3. 配置环境变量**
```bash
cp config_example.env .env
# 编辑 .env，设置 NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD
```

---

## 示例文件

### quick_start.py（推荐入门）

最精简的入门示例，展示完整的基本操作流程：

- 创建项目、文件、类、函数节点
- 建立节点间关系（CONTAINS / DEFINES / HAS_METHOD）
- 查询函数、获取调用链、统计图谱
- 污点流安全分析
- 通过 `graph_db.execute_cypher()` 执行原生 Cypher（逃生舱口）

```bash
# 从 core 目录运行
PYTHONPATH=core python core/example/cagr_processor/graph_dao/quick_start.py
```

### neo4j_usage_example.py（完整功能演示）

完整功能演示，覆盖所有节点类型和关系类型：

- 所有节点类型的创建（Project / File / Class / Function / Variable）
- 所有关系类型的创建（CONTAINS / DEFINES / HAS_METHOD / CALLS / READS / WRITES / TAINT_FLOW_TO）
- 完整查询操作（按名称/全限定名查找、调用链、上下游、污点流、子图）
- 原生 Cypher 查询与高级查询模式
- 事务管理（begin_transaction / commit / rollback）

```bash
PYTHONPATH=core python core/example/cagr_processor/graph_dao/neo4j_usage_example.py
```

### test_config.py

验证当前环境配置是否正确，不做实际数据写入：

```bash
PYTHONPATH=core python core/example/cagr_processor/graph_dao/test_config.py
```

---

## 代码模式

### 标准用法

```python
from cagr_processor.graph_dao.config import GraphDBConfig
from cagr_processor.graph_dao.factory import GraphDBFactory
from cagr_processor.graph_code.models import ProjectNode, FunctionNode, TaintFlowRelationship, RiskLevel
from cagr_processor.graph_code.graph_service import CodeGraphService

# 1. 从环境变量加载配置
config = GraphDBConfig.from_env()

# 2. 创建 DB 层实例，包装为业务层服务
graph_db = GraphDBFactory.create(config)
service = CodeGraphService(graph_db)

try:
    # 3. 通过业务层操作（推荐）
    service.create_project(ProjectNode(name="my-app", language="java", version="1.0.0"))
    service.create_function(FunctionNode(
        qualified_name="com.example.Foo#bar",
        name="bar",
        signature="public String bar(int x)",
        return_type="String",
    ))

    # 查询
    fn = service.find_function_by_name("bar")
    stats = service.get_graph_stats()

    # 4. 需要自定义查询时，通过 DB 层执行原生 Cypher
    results = graph_db.execute_cypher(
        "MATCH (f:Function {name: $name}) RETURN f LIMIT 5",
        {"name": "bar"}
    )
finally:
    graph_db.close()
```

### 节点类型

| 类 | unique_key | 说明 |
|----|-----------|------|
| `ProjectNode` | `name` | 项目根节点 |
| `FileNode` | `path` | 源文件 |
| `ClassNode` | `qualified_name` | 类/接口 |
| `FunctionNode` | `qualified_name` | 函数/方法 |
| `VariableNode` | `qualified_name` | 字段/变量 |

### 关系类型

| 关系 | 起点 → 终点 | 创建方法 |
|------|------------|---------|
| `CONTAINS` | Project → File | `create_project_contains_file()` |
| `DEFINES` | File → Class\|Function | `create_file_defines_class()` / `create_file_defines_function()` |
| `HAS_METHOD` | Class → Function | `create_class_has_method()` |
| `CALLS` | Function → Function | `create_calls_relationship()` |
| `READS` / `WRITES` | Function → Variable | `create_data_access_relationship(access_type="READ"\|"WRITE")` |
| `TAINT_FLOW_TO` | Function → Function | `create_taint_flow_relationship()` |

### 业务查询方法

```python
# 查找函数
service.find_function_by_name("bar")
service.find_function_by_qualified_name("com.example.Foo#bar")

# 调用链分析
service.get_call_chain("com.example.Foo#bar", depth=3)     # 下游调用链
service.get_upstream_callers("com.example.Foo#bar", depth=1)   # 上游调用者
service.get_downstream_callees("com.example.Foo#bar", depth=1) # 下游被调用者

# 安全分析
service.find_taint_flows(source_function="...", sink_function="...", risk_level="High")
service.find_vulnerable_paths("executeQuery")

# 子图（用于 LLM 上下文组装）
service.get_subgraph_for_function("com.example.Foo#bar", depth=2)

# 统计
service.get_graph_stats()  # 返回 GraphStats 对象
```

---

## 环境变量

参考 `config_example.env`：

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
GRAPH_DB_TYPE=neo4j

# 可选连接池参数
NEO4J_MAX_CONNECTION_LIFETIME=3600
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60
```

---

## 常见问题

**连接失败**
```bash
docker ps          # 确认 Neo4j 容器运行中
docker logs neo4j  # 查看 Neo4j 日志
```
确认 URI、用户名、密码与 Neo4j 实际配置一致。

**ModuleNotFoundError**
```bash
# 必须从项目根目录并设置 PYTHONPATH
PYTHONPATH=core python core/example/cagr_processor/graph_dao/quick_start.py
```

**查询超时 / 性能问题**
- 对大批量数据使用 `graph_db.execute_cypher()` 配合 `UNWIND` 批量写入
- 复杂查询添加 `LIMIT` 限制返回量
- 在 Neo4j Browser（`http://localhost:7474`）中为高频查询字段创建索引
