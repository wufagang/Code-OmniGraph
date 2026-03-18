"""Neo4j图数据库实现"""

import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

try:
    from neo4j import GraphDatabase as Neo4jDriver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

from ..base import BaseGraphDatabase
from ..models import (
    ProjectNode, FileNode, ClassNode, FunctionNode, VariableNode,
    CallRelationship, TaintFlowRelationship, DataAccessRelationship,
    GraphStats, SubGraph, NodeLabel, RelType, RiskLevel
)
from cagr_common.exceptions import (
    GraphConnectionException, GraphNodeNotFoundException,
    GraphRelationshipNotFoundException, GraphQueryException
)


class Neo4jDatabase(BaseGraphDatabase):
    """Neo4j图数据库实现"""

    def __init__(self, config):
        super().__init__(config)
        self._driver: Optional[Neo4jDriver] = None
        if not NEO4J_AVAILABLE:
            raise ImportError(
                "Neo4j driver is not installed. "
                "Please install it with: pip install neo4j"
            )

    def connect(self):
        """连接到Neo4j数据库"""
        try:
            self._driver = Neo4jDriver.driver(
                self.config.neo4j_config.uri,
                auth=(self.config.neo4j_config.username, self.config.neo4j_config.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            # 测试连接
            with self._driver.session() as session:
                session.run("RETURN 1")
            self.logger.info("Successfully connected to Neo4j database")
        except Exception as e:
            raise GraphConnectionException(f"Failed to connect to Neo4j: {e}")

    def close(self):
        """关闭数据库连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
            self.logger.info("Neo4j database connection closed")

    def create_project(self, project: ProjectNode) -> bool:
        """创建项目节点"""
        self._ensure_connected()

        query = """
        MERGE (p:Project {name: $name})
        SET p.version = $version,
            p.description = $description,
            p.language = $language,
            p.created_at = datetime()
        RETURN p
        """

        try:
            with self._driver.session() as session:
                session.run(query, {
                    "name": project.name,
                    "version": project.version or "",
                    "description": project.description or "",
                    "language": project.language or ""
                })
            self.logger.info(f"Project '{project.name}' created/updated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create project '{project.name}': {e}")
            raise GraphQueryException(f"Failed to create project: {e}")

    def create_file(self, file: FileNode) -> bool:
        """创建文件节点"""
        self._ensure_connected()

        query = """
        MERGE (f:File {path: $path})
        SET f.name = $name,
            f.language = $language,
            f.size = $size,
            f.last_modified = $last_modified,
            f.content = $content
        WITH f
        MATCH (p:Project {name: $project_name})
        MERGE (p)-[:CONTAINS]->(f)
        RETURN f
        """

        try:
            with self._driver.session() as session:
                session.run(query, {
                    "path": file.path,
                    "name": file.name,
                    "language": file.language,
                    "size": file.size or 0,
                    "last_modified": file.last_modified or "",
                    "content": file.content or "",
                    "project_name": file.project_name or "default"
                })
            self.logger.info(f"File '{file.path}' created/updated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create file '{file.path}': {e}")
            raise GraphQueryException(f"Failed to create file: {e}")

    def create_class(self, class_node: ClassNode) -> bool:
        """创建类节点"""
        self._ensure_connected()

        query = """
        MERGE (c:Class {qualified_name: $qualified_name})
        SET c.name = $name,
            c.package = $package,
            c.modifiers = $modifiers,
            c.superclass = $superclass,
            c.interfaces = $interfaces,
            c.is_abstract = $is_abstract,
            c.is_final = $is_final,
            c.is_interface = $is_interface,
            c.is_enum = $is_enum,
            c.docstring = $docstring,
            c.source_code = $source_code,
            c.lines_of_code = $lines_of_code
        WITH c
        MATCH (f:File {path: $file_path})
        MERGE (f)-[:DEFINES]->(c)
        RETURN c
        """

        try:
            with self._driver.session() as session:
                session.run(query, {
                    "qualified_name": class_node.qualified_name,
                    "name": class_node.name,
                    "package": class_node.package or "",
                    "modifiers": class_node.modifiers or [],
                    "superclass": class_node.superclass or "",
                    "interfaces": class_node.interfaces or [],
                    "is_abstract": class_node.is_abstract or False,
                    "is_final": class_node.is_final or False,
                    "is_interface": class_node.is_interface or False,
                    "is_enum": class_node.is_enum or False,
                    "docstring": class_node.docstring or "",
                    "source_code": class_node.source_code or "",
                    "lines_of_code": class_node.lines_of_code or 0,
                    "file_path": class_node.file_path or ""
                })
            self.logger.info(f"Class '{class_node.qualified_name}' created/updated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create class '{class_node.qualified_name}': {e}")
            raise GraphQueryException(f"Failed to create class: {e}")

    def create_function(self, function: FunctionNode) -> bool:
        """创建函数节点"""
        self._ensure_connected()

        query = """
        MERGE (f:Function {qualified_name: $qualified_name})
        SET f.name = $name,
            f.signature = $signature,
            f.parameters = $parameters,
            f.return_type = $return_type,
            f.modifiers = $modifiers,
            f.is_constructor = $is_constructor,
            f.is_static = $is_static,
            f.is_abstract = $is_abstract,
            f.is_final = $is_final,
            f.is_synchronized = $is_synchronized,
            f.is_native = $is_native,
            f.is_endpoint = $is_endpoint,
            f.body = $body,
            f.docstring = $docstring,
            f.source_code = $source_code,
            f.lines_of_code = $lines_of_code,
            f.cyclomatic_complexity = $cyclomatic_complexity,
            f.start_line = $start_line,
            f.end_line = $end_line
        WITH f
        MATCH (c:Class {qualified_name: $class_name})
        MERGE (c)-[:DECLARES]->(f)
        RETURN f
        """

        try:
            with self._driver.session() as session:
                session.run(query, {
                    "qualified_name": function.qualified_name,
                    "name": function.name,
                    "signature": function.signature or "",
                    "parameters": function.parameters or [],
                    "return_type": function.return_type or "",
                    "modifiers": function.modifiers or [],
                    "is_constructor": function.is_constructor or False,
                    "is_static": function.is_static or False,
                    "is_abstract": function.is_abstract or False,
                    "is_final": function.is_final or False,
                    "is_synchronized": function.is_synchronized or False,
                    "is_native": function.is_native or False,
                    "is_endpoint": function.is_endpoint or False,
                    "body": function.body or "",
                    "docstring": function.docstring or "",
                    "source_code": function.source_code or "",
                    "lines_of_code": function.lines_of_code or 0,
                    "cyclomatic_complexity": function.cyclomatic_complexity or 0,
                    "start_line": function.start_line or 0,
                    "end_line": function.end_line or 0,
                    "class_name": function.class_name or ""
                })
            self.logger.info(f"Function '{function.qualified_name}' created/updated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create function '{function.qualified_name}': {e}")
            raise GraphQueryException(f"Failed to create function: {e}")

    def create_calls_relationship(self, call: CallRelationship) -> bool:
        """创建调用关系"""
        self._ensure_connected()

        query = """
        MATCH (caller:Function {qualified_name: $caller_qualified_name})
        MATCH (callee:Function {qualified_name: $callee_qualified_name})
        MERGE (caller)-[r:CALLS {
            call_site_line: $call_site_line,
            call_site_column: $call_site_column,
            call_type: $call_type,
            created_at: datetime()
        }]->(callee)
        RETURN r
        """

        try:
            with self._driver.session() as session:
                result = session.run(query, {
                    "caller_qualified_name": call.caller_qualified_name,
                    "callee_qualified_name": call.callee_qualified_name,
                    "call_site_line": call.call_site_line or 0,
                    "call_site_column": call.call_site_column or 0,
                    "call_type": call.call_type or "regular"
                })
                if result.single():
                    self.logger.info(f"Call relationship created: {call.caller_qualified_name} -> {call.callee_qualified_name}")
                    return True
                else:
                    raise GraphRelationshipNotFoundException("Failed to create call relationship")
        except Exception as e:
            self.logger.error(f"Failed to create call relationship: {e}")
            raise GraphQueryException(f"Failed to create call relationship: {e}")

    def find_function_by_qualified_name(self, qualified_name: str) -> Optional[FunctionNode]:
        """根据全限定名查找函数"""
        self._ensure_connected()

        query = """
        MATCH (f:Function {qualified_name: $qualified_name})
        RETURN f
        """

        try:
            with self._driver.session() as session:
                result = session.run(query, {"qualified_name": qualified_name})
                record = result.single()
                if record:
                    node_data = record["f"]
                    return FunctionNode(**node_data)
                else:
                    return None
        except Exception as e:
            self.logger.error(f"Failed to find function '{qualified_name}': {e}")
            raise GraphQueryException(f"Failed to find function: {e}")

    def find_taint_flows(self, risk_level: Optional[str] = None,
                        vulnerability_type: Optional[str] = None) -> List[TaintFlowRelationship]:
        """查找污点流"""
        self._ensure_connected()

        query = """
        MATCH (source)-[r:TAINT_FLOW]->(sink)
        WHERE ($risk_level IS NULL OR r.risk = $risk_level)
          AND ($vulnerability_type IS NULL OR r.vulnerability_type = $vulnerability_type)
        RETURN source, r, sink
        """

        try:
            with self._driver.session() as session:
                result = session.run(query, {
                    "risk_level": risk_level,
                    "vulnerability_type": vulnerability_type
                })

                flows = []
                for record in result:
                    flow = TaintFlowRelationship(
                        source_qualified_name=record["source"]["qualified_name"],
                        sink_qualified_name=record["sink"]["qualified_name"],
                        risk=RiskLevel(record["r"]["risk"]),
                        vulnerability_type=record["r"]["vulnerability_type"],
                        data_type=record["r"].get("data_type"),
                        source_line=record["r"].get("source_line"),
                        sink_line=record["r"].get("sink_line")
                    )
                    flows.append(flow)

                return flows
        except Exception as e:
            self.logger.error(f"Failed to find taint flows: {e}")
            raise GraphQueryException(f"Failed to find taint flows: {e}")

    def get_subgraph_for_function(self, qualified_name: str) -> Dict[str, Any]:
        """获取函数子图"""
        self._ensure_connected()

        # 获取中心节点
        center_query = """
        MATCH (f:Function {qualified_name: $qualified_name})
        RETURN f
        """

        # 获取上游调用（调用当前函数的函数）
        upstream_query = """
        MATCH (caller:Function)-[:CALLS]->(f:Function {qualified_name: $qualified_name})
        RETURN caller
        """

        # 获取下游调用（当前函数调用的函数）
        downstream_query = """
        MATCH (f:Function {qualified_name: $qualified_name})-[:CALLS]->(callee:Function)
        RETURN callee
        """

        # 获取相关污点流
        taint_query = """
        MATCH (source)-[r:TAINT_FLOW]->(sink)
        WHERE source.qualified_name = $qualified_name OR sink.qualified_name = $qualified_name
        RETURN source, r, sink
        """

        try:
            with self._driver.session() as session:
                # 获取中心节点
                center_result = session.run(center_query, {"qualified_name": qualified_name})
                center_record = center_result.single()

                if not center_record:
                    raise GraphNodeNotFoundException(f"Function '{qualified_name}' not found")

                center_node = dict(center_record["f"])

                # 获取上游
                upstream_result = session.run(upstream_query, {"qualified_name": qualified_name})
                upstream_nodes = [dict(record["caller"]) for record in upstream_result]

                # 获取下游
                downstream_result = session.run(downstream_query, {"qualified_name": qualified_name})
                downstream_nodes = [dict(record["callee"]) for record in downstream_result]

                # 获取污点流
                taint_result = session.run(taint_query, {"qualified_name": qualified_name})
                taint_flows = []
                for record in taint_result:
                    taint_flows.append({
                        "source": dict(record["source"]),
                        "relationship": dict(record["r"]),
                        "sink": dict(record["sink"])
                    })

                return {
                    "center_node": center_node,
                    "upstream_nodes": upstream_nodes,
                    "downstream_nodes": downstream_nodes,
                    "taint_flows": taint_flows
                }
        except GraphNodeNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get subgraph for function '{qualified_name}': {e}")
            raise GraphQueryException(f"Failed to get subgraph: {e}")

    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行原生Cypher查询"""
        self._ensure_connected()

        try:
            with self._driver.session() as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            self.logger.error(f"Failed to execute Cypher query: {e}")
            raise GraphQueryException(f"Failed to execute Cypher query: {e}")

    def _ensure_connected(self):
        """确保数据库已连接"""
        if not self._driver:
            raise GraphConnectionException("Database is not connected. Please call connect() first.")