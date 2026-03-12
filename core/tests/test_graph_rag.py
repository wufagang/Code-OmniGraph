import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cagr_server.prompt_engine.graph_rag import GraphRAGPipeline

@patch('cagr_server.prompt_engine.graph_rag.QdrantClient')
@patch('cagr_server.prompt_engine.graph_rag.GraphDatabase')
@patch('cagr_server.prompt_engine.graph_rag.ChatOpenAI')
def test_graph_rag_pipeline(mock_llm, mock_neo4j, mock_qdrant):
    # Mock Qdrant semantic search
    mock_qdrant_instance = mock_qdrant.return_value
    mock_qdrant_instance.search.return_value = [
        MagicMock(payload={"method_id": "com.example.UserService.getUser"})
    ]
    
    # Mock Neo4j graph traversal
    mock_neo4j_session = mock_neo4j.driver.return_value.session.return_value.__enter__.return_value
    mock_neo4j_session.run.return_value = [
        {"caller": "com.example.UserController.getUser", "callee": "com.example.UserService.getUser", "table": "users"}
    ]
    
    # Mock LLM response
    mock_llm_instance = mock_llm.return_value
    mock_llm_instance.predict.return_value = "The getUser method queries the users table."
    
    pipeline = GraphRAGPipeline(
        qdrant_url="http://localhost:6333",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        openai_api_key="dummy_key"
    )
    
    answer = pipeline.query("How does user retrieval work?")
    
    assert "getUser method queries the users table" in answer
    mock_qdrant_instance.search.assert_called_once()
    mock_neo4j_session.run.assert_called_once()
    mock_llm_instance.predict.assert_called_once()
