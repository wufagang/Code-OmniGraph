# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 提供在操作本代码仓库时的指导。

## 项目概览

Code-OmniGraph 是一个多维 Java 代码知识图谱系统，结合 Graph-RAG（图检索增强生成）技术，为 LLM 提供精确的代码结构、运行时性能、数据流和业务上下文，实现高精度的代码分析、故障定位和自动重构。

## 架构设计

系统采用双引擎方法：
- **宏观层**（Tree-sitter）：提取项目结构、类、方法和基本关系
- **微观层**（Joern）：执行安全漏洞的数据流分析
- **图存储**（Neo4j）：两层分层图融合
- **向量存储**（Qdrant/Milvus）：方法源代码的语义搜索

## 关键命令

### 开发环境设置
```bash
# 启动基础设施服务
docker-compose -f core/docker-compose.yml up -d

# 安装 Python 依赖
pip install -r core/requirements.txt

# 运行所有测试
python run_tests.py

# 运行特定模块测试
python -m pytest tests/cagr_processor/embedding_worker/ -v
python -m pytest tests/cagr_processor/graph_builder/ -v
python -m pytest tests/collector/ -v
python -m pytest tests/server/ -v

# 生成覆盖率报告
pytest --cov=core tests/

# 启动 Celery 工作进程（异步任务必需）
celery -A core.cagr_processor.tasks worker --loglevel=info

# 启动 FastAPI 服务器
uvicorn core.cagr_server.main:app --reload --host 0.0.0.0 --port 8000
```

### 代码质量
```bash
# 运行代码检查（如已配置）
flake8 core/ --max-line-length=100

# 类型检查（如已配置）
mypy core/cagr_processor/core/cagr_server/ --ignore-missing-imports
```

## 模块结构

### `/core/cagr_collector/` - 数据收集
- `static_analyzer/joern_parser.py`：Joern CLI 包装器，用于 CPG 生成
- `static_analyzer/tree_sitter_parser.py`：多语言 AST 解析
- `schema_inspector/mybatis_parser.py`：MyBatis XML 关系提取
- `dynamic_observer/skywalking_client.py`：运行时指标收集
- `context_scraper/git_scraper.py`：Git 历史和 Jira 集成

### `/core/cagr_processor/` - 数据处理
- `graph_builder/`：Neo4j 图数据库抽象层
  - `interfaces.py`：GraphDatabase 抽象接口
  - `impl/neo4j_impl.py`：带 Cypher 查询的 Neo4j 实现
  - `models.py`：领域模型（NodeLabel、RelType、FunctionNode 等）
  - `factory.py`：用于实例创建的 GraphDBFactory
- `embedding_worker/`：向量数据库抽象（Qdrant/Milvus）
  - 统一接口，带批量操作和错误处理
  - 数据库选择的工厂模式
- `tasks.py`：异步处理的 Celery 任务

### `/core/cagr_server/` - API 层
- `main.py`：FastAPI 路由和 Graph-RAG 管道
- `prompt_engine/graph_rag.py`：LLM 查询的 LangChain 集成

### `/core/cagr_common/` - 共享模型
- Project、Class、Method、Table 等的 Pydantic 模型
- 方法调用和数据操作的关系模型
### /core/tests/** - 测试用例和固件
- 所有的模块测试代码全部写这个模块下，并且按照不同的模块进行分类
- 所有新方法必新增单元测试，并且能通过
- 所有修改方法同步更新单元测试，并且能通过
- 测试框架使用 pytest，统一放在 tests/ 目录下
- 测试目录结构：
  - `tests/cagr_processor/embedding_worker/` - 向量数据库测试
  - `tests/cagr_processor/graph_builder/` - 图数据库测试
  - `tests/collector/` - 数据收集器测试
  - `tests/server/` - API 服务测试

## 设计模式

### 图数据库模式
所有图操作遵循以下模式：
1. 使用 `GraphDBConfig.from_env()` 创建配置
2. 通过 `GraphDBFactory.create(config)` 获取实例
3. 使用抽象 `GraphDatabase` 接口方法
4. 批量操作使用 UNWIND Cypher 以提高性能

### 向量数据库模式
向量数据库的类似抽象：
1. 通过 `VectorDBConfig` 配置
2. 使用 `VectorDBFactory` 工厂创建
3. 统一的插入/搜索/删除操作接口
4. 内置重试机制和错误处理

### 模型模式
所有数据模型使用 Pydantic 进行验证：
- 输入验证和序列化
- 带类型的清晰字段定义
- 灵活的可选字段

## 环境配置

配置从 `.env` 文件按以下优先级加载：
1. 当前工作目录
2. 父目录
3. `/core/` 目录
4. 仓库根目录

关键环境变量：
```bash
# 图数据库
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# 向量数据库
VECTOR_DB_TYPE=qdrant  # 或 milvus
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis（Celery）
REDIS_URL=redis://localhost:6379/0
```

## 测试方法

- **单元测试**：每个模块都有相应的测试
- **模拟策略**：外部服务（Neo4j、Qdrant）被模拟
- **测试数据**：使用固件确保一致的测试场景
- **覆盖率**：核心模块目标 >90% 覆盖率

## 常见开发任务

### 添加新的图数据库后端
1. 在 `/graph_builder/impl/` 中创建实现
2. 继承自 `BaseGraphDatabase`
3. 实现 `GraphDatabase` 的所有抽象方法
4. 在 `GraphDBFactory._registry` 中注册
5. 在 `config.py` 中添加配置模型

### 添加新的向量数据库后端
1. 实现 `VectorDatabase` 接口
2. 添加配置模型
3. 在 `VectorDBFactory` 中注册
4. 按照现有模式创建测试

### 修改图模式
1. 更新 `/graph_builder/models.py` 中的模型
2. 更新实现中的 Cypher 查询
3. 如需要，添加迁移脚本
4. 用新模式更新测试

## 重要说明

- 始终对大型导入使用批量操作（Neo4j 中的 UNWIND）
- 连接池自动处理
- 内置重试机制处理瞬时故障
- 图操作是事务性的
- 向量操作同时支持稠密和稀疏向量