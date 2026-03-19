# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Code-OmniGraph is a multi-dimensional Java code knowledge graph system that combines Graph-RAG technology to provide precise code structure, runtime performance, data flow, and business context for LLMs to achieve high-accuracy code analysis, fault location, and automatic refactoring.

## Architecture

The system uses a dual-engine approach:
- **Macro Layer** (Tree-sitter): Extracts project structure, classes, methods, and basic relationships
- **Micro Layer** (Joern): Performs data-flow analysis for security vulnerabilities
- **Graph Storage** (Neo4j): Hierarchical graph fusion of both layers
- **Vector Storage** (Qdrant/Milvus): Semantic search for method source code

## Key Commands

### Development Setup
```bash
# Start infrastructure services
docker-compose -f core/docker-compose.yml up -d

# Install Python dependencies
pip install -r core/requirements.txt

# Run all tests
python core/run_tests.py

# Run specific test module
python -m pytest core/cagr_processor/graph_builder/tests/test_neo4j_impl.py -v
python -m pytest core/cagr_processor/embedding_dao/tests/ -v

# Start Celery worker (required for async tasks)
celery -A core.cagr_processor.tasks worker --loglevel=info

# Start FastAPI server
uvicorn core.cagr_server.main:app --reload --host 0.0.0.0 --port 8000
```

### Code Quality
```bash
# Run linting (if configured)
flake8 core/ --max-line-length=100

# Type checking (if configured)
mypy core/cagr_processor/core/cagr_server/ --ignore-missing-imports
```

## Module Structure

### `/core/cagr_collector/` - Data Collection
- `static_analyzer/joern_parser.py`: Joern CLI wrapper for CPG generation
- `static_analyzer/tree_sitter_parser.py`: Multi-language AST parsing
- `schema_inspector/mybatis_parser.py`: MyBatis XML relationship extraction
- `dynamic_observer/skywalking_client.py`: Runtime metrics collection
- `context_scraper/git_scraper.py`: Git history and Jira integration

### `/core/cagr_processor/` - Data Processing
- `graph_builder/`: Neo4j graph database abstraction layer
  - `interfaces.py`: GraphDatabase abstract interface
  - `impl/neo4j_impl.py`: Neo4j implementation with Cypher queries
  - `models.py`: Domain models (NodeLabel, RelType, FunctionNode, etc.)
  - `factory.py`: GraphDBFactory for instance creation
- `embedding_worker/`: Vector database abstraction (Qdrant/Milvus)
  - Unified interface with batch operations and error handling
  - Factory pattern for database selection
- `tasks.py`: Celery tasks for async processing

### `/core/cagr_server/` - API Layer
- `main.py`: FastAPI routes and Graph-RAG pipeline
- `prompt_engine/graph_rag.py`: LangChain integration for LLM queries

### `/core/cagr_common/` - Shared Models
- Pydantic models for Project, Class, Method, Table, etc.
- Relationship models for method calls and data operations

## Design Patterns

### Graph Database Pattern
All graph operations follow this pattern:
1. Create configuration with `GraphDBConfig.from_env()`
2. Get instance via `GraphDBFactory.create(config)`
3. Use abstract `GraphDatabase` interface methods
4. Batch operations use UNWIND Cypher for performance

### Vector Database Pattern
Similar abstraction for vector databases:
1. Configuration via `VectorDBConfig`
2. Factory creation with `VectorDBFactory`
3. Unified interface for insert/search/delete operations
4. Retry mechanisms and error handling built-in

### Model Pattern
All data models use Pydantic for validation:
- Input validation and serialization
- Clear field definitions with types
- Optional fields for flexibility

## Environment Configuration

Configuration is loaded from `.env` files in this priority:
1. Current working directory
2. Parent directory
3. `/core/` directory
4. Repository root

Key environment variables:
```bash
# Graph Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Vector Database
VECTOR_DB_TYPE=qdrant  # or milvus
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0
```

## Testing Approach

- **Unit Tests**: Each module has corresponding tests
- **Mock Strategy**: External services (Neo4j, Qdrant) are mocked
- **Test Data**: Use fixtures for consistent test scenarios
- **Coverage**: Aim for >90% coverage on core modules

## Common Development Tasks

### Adding a New Graph Database Backend
1. Create implementation in `/graph_builder/impl/`
2. Inherit from `BaseGraphDatabase`
3. Implement all abstract methods from `GraphDatabase`
4. Register in `GraphDBFactory._registry`
5. Add configuration model in `config.py`

### Adding a New Vector Database Backend
1. Implement `VectorDatabase` interface
2. Add configuration model
3. Register in `VectorDBFactory`
4. Create tests following existing patterns

### Modifying Graph Schema
1. Update models in `/graph_builder/models.py`
2. Update Cypher queries in implementation
3. Add migration scripts if needed
4. Update tests with new schema

## Important Notes

- Always use batch operations for large imports (UNWIND in Neo4j)
- Connection pooling is handled automatically
- Retry mechanisms are built-in for transient failures
- Graph operations are transactional
- Vector operations support both dense and sparse vectors