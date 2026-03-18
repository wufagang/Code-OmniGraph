import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ.setdefault('VECTOR_DB_TYPE', 'qdrant')
os.environ.setdefault('QDRANT_HOST', 'localhost')
os.environ.setdefault('QDRANT_PORT', '6333')
os.environ.setdefault('NEO4J_URI', 'bolt://localhost:7687')
os.environ.setdefault('NEO4J_USERNAME', 'neo4j')
os.environ.setdefault('NEO4J_PASSWORD', 'password')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')

# pytest配置
def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")