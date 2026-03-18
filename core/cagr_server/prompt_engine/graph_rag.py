from qdrant_client import QdrantClient
from neo4j import GraphDatabase
import openai
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class GraphRAGPipeline:
    def __init__(self, qdrant_url: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str, openai_api_key: str):
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.openai_client = openai.OpenAI(api_key=openai_api_key)

        self.prompt_template = """You are an expert Java system architect. Answer the user's query based on the following code graph context.

Context:
{context}

Query: {query}

Answer:
"""

    def retrieve_method_id_from_vector(self, query: str) -> str:
        # In a real scenario, embed the query using an embedding model
        # Here we mock the embedding vector
        dummy_vector = [0.1] * 768
        
        search_result = self.qdrant_client.search(
            collection_name="methods",
            query_vector=dummy_vector,
            limit=1
        )
        if search_result:
            return search_result[0].payload.get("method_id")
        return None

    def retrieve_graph_context(self, method_id: str) -> str:
        cypher_query = """
        MATCH (m:Method {id: $method_id})-[r:STATIC_CALLS*1..3]-(related:Method)
        OPTIONAL MATCH (m)-[:OPERATES]->(t:Table)
        RETURN m.name AS method, related.name AS related_method, t.name AS table
        LIMIT 50
        """
        
        context_lines = []
        with self.neo4j_driver.session() as session:
            result = session.run(cypher_query, method_id=method_id)
            for record in result:
                method = record.get("method")
                related = record.get("related_method")
                table = record.get("table")
                
                line = f"Method {method} calls {related}."
                if table:
                    line += f" It operates on table {table}."
                context_lines.append(line)
                
        return "\n".join(context_lines)

    def query(self, user_query: str) -> str:
        # Step 1: Semantic Search
        method_id = self.retrieve_method_id_from_vector(user_query)

        if not method_id:
            return "No relevant code found."

        # Step 2: Graph Traversal
        graph_context = self.retrieve_graph_context(method_id)

        # Step 3: LLM Generation
        prompt = self.prompt_template.format(query=user_query, context=graph_context)
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content
