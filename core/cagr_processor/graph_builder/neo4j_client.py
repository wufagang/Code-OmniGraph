from neo4j import GraphDatabase
from typing import List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from cagr_common.models import Method, MethodCall

class Neo4jBuilder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def insert_methods(self, methods: List[Method]):
        with self.driver.session() as session:
            for method in methods:
                session.run(
                    "MERGE (m:Method {id: $id}) "
                    "SET m.name = $name, m.signature = $signature, m.className = $class_name",
                    id=method.id, name=method.name, signature=method.signature, class_name=method.class_name
                )

    def insert_calls(self, calls: List[MethodCall]):
        with self.driver.session() as session:
            for call in calls:
                session.run(
                    "MATCH (caller:Method {id: $caller_id}) "
                    "MATCH (callee:Method {id: $callee_id}) "
                    "MERGE (caller)-[r:STATIC_CALLS]->(callee) "
                    "SET r.qps = $qps, r.latency = $latency",
                    caller_id=call.caller_id, callee_id=call.callee_id, qps=call.qps, latency=call.latency
                )
