# Code-OmniGraph Neo4j 图数据库使用示例

这个目录包含了使用 Code-OmniGraph 的 Neo4j 图数据库模块的完整示例。

## 前提条件

1. 安装 Neo4j 数据库（建议使用 Docker）
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

2. 安装 Python 依赖
```bash
pip install -r core/requirements.txt
```

3. 配置环境变量
```bash
cp config_example.env .env
# 编辑 .env 文件，设置正确的 Neo4j 连接信息
```

## 示例文件说明

### 1. quick_start.py
最简洁的入门示例，展示基本用法：
- 连接 Neo4j 数据库
- 创建节点（项目、文件、类、函数）
- 创建关系
- 基本查询操作

运行：
```bash
python quick_start.py
```

### 2. neo4j_usage_example.py
完整的功能演示，展示所有 API 的用法：
- 所有节点类型的创建
- 所有关系类型的创建
- 各种查询操作
- 事务处理
- 高级 Cypher 查询
- 安全分析（污点流）

运行：
```bash
python neo4j_usage_example.py
```

## 核心概念

### 图数据库抽象层

Code-OmniGraph 提供了一个抽象的图数据库接口，支持：

1. **节点类型**：
   - Project（项目）
   - File（文件）
   - Class（类）
   - Function（函数）
   - Variable（变量）

2. **关系类型**：
   - CONTAINS（包含）
   - DEFINES（定义）
   - HAS_METHOD（包含方法）
   - CALLS（调用）
   - READS/WRITES（读写变量）
   - TAINT_FLOW_TO（污点流）

3. **查询能力**：
   - 根据名称查找函数
   - 获取调用链
   - 查找上游/下游函数
   - 安全漏洞路径分析
   - 子图提取

### 使用模式

```python
from core.cagr_processor.graph_builder.config import GraphDBConfig
from core.cagr_processor.graph_builder.factory import GraphDBFactory

# 1. 创建配置
config = GraphDBConfig.from_env()

# 2. 创建数据库实例
graph_db = GraphDBFactory.create(config)

# 3. 连接数据库
graph_db.connect()

# 4. 执行操作
try:
    # 创建节点、关系、查询等
    pass
finally:
    # 5. 关闭连接
    graph_db.close()
```

## 实际应用场景

### 1. 代码分析
构建代码知识图谱，分析：
- 函数调用关系
- 类继承层次
- 依赖关系图

### 2. 安全分析
通过污点流分析发现：
- SQL 注入漏洞
- XSS 漏洞
- 命令注入漏洞

### 3. 代码重构
利用图结构进行：
- 影响分析
- 重构建议
- 代码质量评估

### 4. 智能问答
结合 Graph-RAG 技术：
- 代码语义搜索
- 智能代码补全
- 问题定位

## 性能优化建议

1. **批量操作**：使用批量 API 减少网络往返
2. **索引优化**：为常用查询字段创建索引
3. **查询优化**：合理使用查询深度限制
4. **连接池**：复用数据库连接

## 故障排除

### 连接失败
- 检查 Neo4j 服务是否运行
- 验证连接 URI、用户名和密码
- 确保防火墙允许连接

### 查询超时
- 增加查询超时时间
- 优化复杂查询
- 添加适当的索引

### 内存问题
- 限制查询返回的结果数量
- 使用分页查询
- 调整 Neo4j 内存配置

## 扩展阅读

- [Neo4j 官方文档](https://neo4j.com/docs/)
- [Cypher 查询语言](https://neo4j.com/docs/cypher-manual/)
- [Code-OmniGraph 架构文档](../../docs/)