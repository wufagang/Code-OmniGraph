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

## Setup & Running

1. **Start Infrastructure (Neo4j, Qdrant, Redis):**
   ```bash
   docker-compose up -d
   ```

2. **Install Dependencies:**
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
