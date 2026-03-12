from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from typing import List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from cagr_common.models import Method

class QdrantWorker:
    def __init__(self, url: str):
        self.client = QdrantClient(url=url)
        self.collection_name = "methods"
        
        # Ensure collection exists
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )

    def embed_and_upsert(self, methods: List[Method]):
        # In a real scenario, use an embedding model (e.g., HuggingFace or OpenAI)
        # Here we mock the embedding process
        points = []
        for i, method in enumerate(methods):
            dummy_vector = [0.1] * 768
            points.append(
                PointStruct(
                    id=i,
                    vector=dummy_vector,
                    payload={"method_id": method.id, "name": method.name, "class": method.class_name}
                )
            )
            
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
