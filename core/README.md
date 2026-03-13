# Code-OmniGraph

Code-OmniGraph (全知代码图谱) is a multi-dimensional Java code knowledge graph system combined with Graph-RAG technology. It provides precise code structure, runtime performance, data flow, and business context for LLMs to achieve high-accuracy code analysis, fault location, and automatic refactoring.

## Architecture

- **Backend:** Python 3.10+ (FastAPI)
- **Graph Database:** Neo4j (Stores topology and metadata)
- **Vector Database:** Qdrant (Stores method source code and semantic vectors)
- **Analysis Engine:** Joern (CPG generation), Tree-sitter (incremental parsing)
- **AI Orchestration:** LangChain (Graph-RAG pipeline)
- **Task Scheduling:** Celery + Redis (Handles large-scale code scanning)

## Directory Structure

- `cagr-collector/`: Data collection module (Static Analyzer, Dynamic Observer, Schema Inspector, Context Scraper)
- `cagr-processor/`: Data cleaning and graph modeling (Neo4j Builder, Qdrant Worker, Celery Tasks)
- `cagr-common/`: Common models (Pydantic schemas)
- `cagr-server/`: RAG API interface (FastAPI, LangChain Prompt Engine)
- `tests/`: Pytest test cases


## 核心完成模块：
1. 项目骨架与基础设施：
- docker-compose.yml：配置了 Neo4j 5.x、Qdrant 和 Redis 7。
- requirements.txt：包含了 FastAPI, Neo4j, Qdrant-client, LangChain, Celery, Redis, GitPython 等核心依赖。
- cagr_common/models.py：基于 Pydantic 定义了 Class, Method, Table, Commit, JiraIssue 等核心图谱节点和关系模型。
2. Module 1: 静态解析引擎 (Static Ingestion)
- cagr_collector/static_analyzer/joern_parser.py：封装了 Joern CLI 调用，提取 AST 方法和调用链。
- cagr_collector/static_analyzer/tree_sitter_parser.py：预留了基于 Tree-sitter 的增量解析逻辑。
3. Module 2: 数据流映射器 (Data Schema Mapper)
- cagr_collector/schema_inspector/mybatis_parser.py：解析 MyBatis XML 文件，通过正则提取 SQL 中的 TABLE_NAME，建立 (Method)-[:OPERATES]->(Table) 关系。
4. Module 3: 动态指标集成 (APM Integrator)
- cagr_collector/dynamic_observer/skywalking_client.py：对接 SkyWalking GraphQL API，拉取 Trace 统计数据（耗时、QPS）。
5. Module 4: 业务上下文提取 (Git Scraper)
- cagr_collector/context_scraper/git_scraper.py：使用 GitPython 遍历 Git 提交历史，通过正则提取 Jira ID。
6. Module 5: Graph-RAG 推理层
- cagr_server/prompt_engine/graph_rag.py：使用 LangChain 实现了多级检索 Pipeline。先从 Qdrant 向量库进行语义检索获取 Method ID，再通过 Cypher 语句从 Neo4j 扩展 3 层调用链和数据库表，最后组装 Prompt 喂给大模型（GPT-4o）。
7. 异步任务与 API 接口
- cagr_processor/tasks.py：使用 Celery + Redis 实现了异步代码扫描任务。
- cagr_server/main.py：基于 FastAPI 提供了 /api/v1/scan（触发扫描）、/api/v1/scan/{task_id}（查询进度）和 /api/v1/query（Graph-RAG 问答）接口。
8. 单元测试 (Pytest)
- tests/test_models.py：测试 Pydantic 数据模型。
- tests/test_static_analyzer.py：Mock Joern 输出，测试方法和调用链提取。
- tests/test_graph_rag.py：Mock Qdrant、Neo4j 和 LLM，测试完整的 Graph-RAG 检索和回答链路。
- tests/test_integrations.py：测试 SkyWalking API 和 GitPython 解析。
如何在本地运行与测试：
您可以点击编辑器左侧的文件树，查看 code-omnigraph 目录下的所有源码。将该目录导出到本地后，执行以下命令：

## Setup & Running

1. **Start Infrastructure (Neo4j, Qdrant, Redis):**
   ```bash
   docker-compose up -d
   ```

2. **Install Dependencies:**
   ```bash
   cd core
   ```
   
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Tests:**
   ```bash
   python run_tests.py
   ```

4. **Start Celery Worker:**
   ```bash
   celery -A cagr_processor.tasks worker --loglevel=info
   ```

5. **Start FastAPI Server:**
   ```bash
   uvicorn cagr_server.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

- `POST /api/v1/scan`: Trigger an asynchronous code scan task.
- `GET /api/v1/scan/{task_id}`: Check the progress of a scan task.
- `POST /api/v1/query`: Query the Graph-RAG system with a natural language question.
- `GET /health`: Health check endpoint.
