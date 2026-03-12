from celery import Celery
import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("cagr_tasks", broker=redis_url, backend=redis_url)

@celery_app.task(bind=True)
def run_code_scan(self, project_path: str):
    # Mocking a long-running scan task
    self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': 'Starting scan...'})
    time.sleep(2)
    
    self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100, 'status': 'Parsing AST with Joern...'})
    time.sleep(3)
    
    self.update_state(state='PROGRESS', meta={'current': 60, 'total': 100, 'status': 'Extracting APM and Git context...'})
    time.sleep(3)
    
    self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100, 'status': 'Building Graph in Neo4j and Qdrant...'})
    time.sleep(2)
    
    return {'current': 100, 'total': 100, 'status': 'Scan completed successfully', 'project_path': project_path}
