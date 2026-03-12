from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cagr_server.prompt_engine.graph_rag import GraphRAGPipeline
from cagr_processor.tasks import run_code_scan, celery_app

app = FastAPI(title="Code-OmniGraph API", version="1.0.0")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str

class ScanRequest(BaseModel):
    project_path: str

class ScanResponse(BaseModel):
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    status: str
    progress: int

# Initialize pipeline (mocking credentials for demonstration)
pipeline = GraphRAGPipeline(
    qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
    neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
    openai_api_key=os.getenv("OPENAI_API_KEY", "dummy_key")
)

@app.post("/api/v1/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest):
    task = run_code_scan.delay(request.project_path)
    return ScanResponse(task_id=task.id)

@app.get("/api/v1/scan/{task_id}", response_model=TaskStatusResponse)
async def get_scan_status(task_id: str):
    task_result = celery_app.AsyncResult(task_id)
    state = task_result.state
    
    if state == 'PENDING':
        response = {
            'state': state,
            'status': 'Pending...',
            'progress': 0
        }
    elif state != 'FAILURE':
        response = {
            'state': state,
            'status': task_result.info.get('status', '') if task_result.info else '',
            'progress': task_result.info.get('current', 0) if task_result.info else 0
        }
        if 'result' in task_result.info:
            response['result'] = task_result.info['result']
    else:
        response = {
            'state': state,
            'status': str(task_result.info),
            'progress': 0
        }
        
    return TaskStatusResponse(
        task_id=task_id,
        state=response['state'],
        status=response['status'],
        progress=response['progress']
    )

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_graph(request: QueryRequest):
    try:
        answer = pipeline.query(request.query)
        return QueryResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
