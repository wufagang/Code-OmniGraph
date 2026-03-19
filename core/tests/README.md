# 测试目录结构

本测试目录包含 Code-OmniGraph 项目的所有测试用例，按照模块结构组织。

## 目录结构

```
tests/
├── conftest.py                    # pytest 配置文件和共享测试设置
├── cagr_processor/                # 处理器模块测试
│   ├── embedding_worker/          # 向量数据库模块测试
│   │   ├── test_base.py          # 基础向量数据库测试
│   │   ├── test_config.py        # 配置测试
│   │   ├── test_factory.py       # 工厂模式测试
│   │   ├── test_models.py        # 模型测试
│   │   └── test_qdrant_impl.py   # Qdrant 实现测试
│   └── graph_dao/             # 图数据库模块测试
│       └── test_neo4j_impl.py     # Neo4j 实现测试
├── collector/                     # 数据收集模块测试
│   └── test_tree_sitter_parser.py  # Tree-sitter 解析器测试
└── server/                        # API 服务模块测试
    ├── test_graph_rag.py         # Graph-RAG 流程测试
    ├── test_integrations.py      # 集成测试
    ├── test_models.py            # 模型测试
    └── test_static_analyzer.py   # 静态分析器测试
```

## 测试框架

所有测试使用 pytest 框架，包含以下特性：

- **统一配置**：通过 `conftest.py` 提供共享配置和测试环境
- **Mock 支持**：大量使用 mock 对象模拟外部依赖（Neo4j、Qdrant、外部服务）
- **并行执行**：支持 pytest-xdist 插件进行并行测试
- **覆盖率报告**：支持 pytest-cov 插件生成覆盖率报告

## 运行测试

### 运行所有测试
```bash
python run_tests.py
```

### 运行特定模块测试
```bash
# 运行向量数据库测试
python -m pytest tests/cagr_processor/embedding_worker/ -v

# 运行图数据库测试
python -m pytest tests/cagr_processor/graph_dao/ -v

# 运行数据收集器测试
python -m pytest tests/collector/ -v

# 运行API服务测试
python -m pytest tests/server/ -v

# 运行特定测试文件
python -m pytest tests/cagr_processor/embedding_worker/test_base.py -v
```

### 生成覆盖率报告
```bash
pytest --cov=core tests/
```

## 测试覆盖率

当前测试覆盖率：

- **cagr_processor/embedding_worker**: 95%+ 覆盖率
- **cagr_processor/graph_dao**: 90%+ 覆盖率（Neo4jDatabase 为抽象类，使用 mock 测试）
- **collector**: 由于 tree-sitter 依赖，部分测试需要外部库
- **server**: 基础测试覆盖

## 外部依赖

### 必需依赖
- `pytest`: 测试框架
- `pytest-cov`: 覆盖率插件
- `pytest-xdist`: 并行执行插件

### 可选依赖
- `tree-sitter`: 代码解析（collector 模块）
- `tree-sitter-python`: Python 语法支持
- `tree-sitter-java`: Java 语法支持
- `neo4j`: Neo4j 图数据库驱动
- `qdrant-client`: Qdrant 向量数据库客户端
- `pymilvus`: Milvus 向量数据库客户端

## Mock 测试策略

由于涉及外部数据库和服务，大量测试使用 mock 对象：

1. **数据库连接**：使用 `unittest.mock.Mock` 模拟数据库连接
2. **外部服务**：模拟 API 调用和响应
3. **文件系统**：使用临时目录进行测试
4. **配置加载**：模拟环境变量和配置文件

## 测试最佳实践

1. **隔离性**：每个测试应该独立运行，不依赖其他测试
2. **可重复性**：测试结果应该可重复，不受外部环境影响
3. **快速执行**：使用 mock 避免真实的外部调用
4. **清晰断言**：使用明确的断言语句，便于理解测试意图

## 新增测试指南

1. 在对应模块的测试目录下创建测试文件
2. 使用 `test_` 前缀命名测试函数
3. 遵循现有测试的结构和命名约定
4. 使用 mock 模拟外部依赖
5. 为每个测试提供清晰的文档字符串

## 已知问题

1. **Neo4jDatabase 抽象类**：当前为抽象类，缺少部分方法实现，测试使用 mock 实现
2. **Tree-sitter 依赖**：collector 模块测试需要安装 tree-sitter 及其语言库
3. **外部服务依赖**：部分集成测试需要真实的外部服务连接

## 后续改进

1. 完善 Neo4jDatabase 的具体实现
2. 添加更多集成测试
3. 提高测试覆盖率到 95%+
4. 添加性能测试
5. 添加端到端测试