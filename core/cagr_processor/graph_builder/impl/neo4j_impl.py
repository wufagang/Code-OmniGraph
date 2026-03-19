"""Neo4j图数据库完整实现 - 包含所有抽象方法"""

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


class _Neo4jTransaction:
    """持有 session 和 transaction，确保 session 在事务结束后正确关闭"""

    def __init__(self, session, tx):
        self._session = session
        self._tx = tx

    def commit(self):
        try:
            self._tx.commit()
        finally:
            self._session.close()

    def rollback(self):
        try:
            self._tx.rollback()
        finally:
            self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        return False


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

    def _ensure_connected(self):
        """确保数据库已连接"""
        if not self._driver:
            raise GraphConnectionException("Database is not connected. Please call connect() first.")

    def _validate_connection(self):
        """重写基类验证方法，检查 Neo4j driver 而非 _connection"""
        self._ensure_connected()

    # 事务管理方法
    def begin_transaction(self):
        """开始事务，返回 _Neo4jTransaction 包装对象"""
        self._ensure_connected()
        session = self._driver.session()
        try:
            tx = session.begin_transaction()
            return _Neo4jTransaction(session, tx)
        except Exception:
            session.close()
            raise

    def commit(self, tx) -> None:
        """提交事务"""
        if isinstance(tx, _Neo4jTransaction):
            tx.commit()
        elif hasattr(tx, 'commit'):
            tx.commit()

    def rollback(self, tx) -> None:
        """回滚事务"""
        if isinstance(tx, _Neo4jTransaction):
            tx.rollback()
        elif hasattr(tx, 'rollback'):
            tx.rollback()

    def clear_graph(self):
        """清空整个图谱（谨慎使用）"""
        self._ensure_connected()
        query = "MATCH (n) DETACH DELETE n"
        try:
            with self._driver.session() as session:
                session.run(query)
            self.logger.warning("Graph has been cleared!")
        except Exception as e:
            self.logger.error(f"Failed to clear graph: {e}")
            raise GraphQueryException(f"Failed to clear graph: {e}")

    # 查询方法实现
    def find_function_by_name(self, name: str) -> Optional[FunctionNode]:
        """根据函数名查找函数节点"""
        self._ensure_connected()

        query = """
        MATCH (f:Function {name: $name})
        RETURN f
        LIMIT 1
        """

        try:
            with self._driver.session() as session:
                result = session.run(query, {"name": name})
                record = result.single()
                if record:
                    node_data = dict(record["f"])
                    return FunctionNode(**node_data)
                return None
        except Exception as e:
            self.logger.error(f"Failed to find function by name '{name}': {e}")
            raise GraphQueryException(f"Failed to find function: {e}")

    def get_call_chain(self, function_qualified_name: str, depth: int = 3) -> List[Dict[str, Any]]:
        """获取函数调用链"""
        self._ensure_connected()

        query = """
        MATCH path = (start:Function {qualified_name: $qualified_name})-[:CALLS*..%d]->(end:Function)
        RETURN [n in nodes(path) | {
            qualified_name: n.qualified_name,
            name: n.name,
            signature: n.signature
        }] as chain
        """ % depth

        try:
            with self._driver.session() as session:
                result = session.run(query, {"qualified_name": function_qualified_name})
                chains = []
                for record in result:
                    chains.append(record["chain"])
                return chains
        except Exception as e:
            self.logger.error(f"Failed to get call chain for '{function_qualified_name}': {e}")
            raise GraphQueryException(f"Failed to get call chain: {e}")

    def get_upstream_callers(self, function_qualified_name: str, depth: int = 1) -> List[Dict[str, Any]]:
        """获取上游调用者"""
        self._ensure_connected()

        query = """
        MATCH path = (caller:Function)-[:CALLS*..%d]->(target:Function {qualified_name: $qualified_name})
        RETURN DISTINCT {
            qualified_name: caller.qualified_name,
            name: caller.name,
            signature: caller.signature
        } as caller
        """ % depth

        try:
            with self._driver.session() as session:
                result = session.run(query, {"qualified_name": function_qualified_name})
                callers = []
                for record in result:
                    callers.append(record["caller"])
                return callers
        except Exception as e:
            self.logger.error(f"Failed to get upstream callers for '{function_qualified_name}': {e}")
            raise GraphQueryException(f"Failed to get upstream callers: {e}")

    def get_downstream_callees(self, function_qualified_name: str, depth: int = 1) -> List[Dict[str, Any]]:
        """获取下游被调用者"""
        self._ensure_connected()

        query = """
        MATCH path = (caller:Function {qualified_name: $qualified_name})-[:CALLS*..%d]->(callee:Function)
        RETURN DISTINCT {
            qualified_name: callee.qualified_name,
            name: callee.name,
            signature: callee.signature
        } as callee
        """ % depth

        try:
            with self._driver.session() as session:
                result = session.run(query, {"qualified_name": function_qualified_name})
                callees = []
                for record in result:
                    callees.append(record["callee"])
                return callees
        except Exception as e:
            self.logger.error(f"Failed to get downstream callees for '{function_qualified_name}': {e}")
            raise GraphQueryException(f"Failed to get downstream callees: {e}")

    def get_graph_stats(self) -> GraphStats:
        """获取图谱统计信息"""
        self._ensure_connected()

        queries = {
            "total_nodes": "MATCH (n) RETURN count(n) as count",
            "total_relationships": "MATCH ()-[r]->() RETURN count(r) as count",
            "projects": "MATCH (n:Project) RETURN count(n) as count",
            "files": "MATCH (n:File) RETURN count(n) as count",
            "classes": "MATCH (n:Class) RETURN count(n) as count",
            "functions": "MATCH (n:Function) RETURN count(n) as count",
            "variables": "MATCH (n:Variable) RETURN count(n) as count"
        }

        try:
            stats = GraphStats()
            with self._driver.session() as session:
                # 总节点数
                result = session.run(queries["total_nodes"])
                stats.total_nodes = result.single()["count"]

                # 总关系数
                result = session.run(queries["total_relationships"])
                stats.total_relationships = result.single()["count"]

                # 各类节点统计
                stats.node_counts = {}
                for node_type, query in queries.items():
                    if node_type not in ["total_nodes", "total_relationships"]:
                        result = session.run(query)
                        count = result.single()["count"]
                        stats.node_counts[node_type] = count

            return stats
        except Exception as e:
            self.logger.error(f"Failed to get graph stats: {e}")
            raise GraphQueryException(f"Failed to get graph stats: {e}")

    def find_vulnerable_paths(self, sink_function_name: str) -> List[List[Dict[str, Any]]]:
        """查找到达危险函数的所有路径"""
        self._ensure_connected()

        query = """
        MATCH path = (start:Function)-[:CALLS*]->(sink:Function {name: $sink_function_name})
        WHERE start <> sink
        RETURN [n in nodes(path) | {
            qualified_name: n.qualified_name,
            name: n.name
        }] as path
        """

        try:
            with self._driver.session() as session:
                result = session.run(query, {"sink_function_name": sink_function_name})
                paths = []
                for record in result:
                    paths.append(record["path"])
                return paths
        except Exception as e:
            self.logger.error(f"Failed to find vulnerable paths to '{sink_function_name}': {e}")
            raise GraphQueryException(f"Failed to find vulnerable paths: {e}")

    # 重用已有的方法实现
    def create_project(self, project: ProjectNode) -> bool:
        """创建项目节点"""
        return super().create_project(project)

    def create_file(self, file: FileNode) -> bool:
        """创建文件节点"""
        return super().create_file(file)

    def create_class(self, class_node: ClassNode) -> bool:
        """创建类节点"""
        return super().create_class(class_node)

    def create_function(self, function: FunctionNode) -> bool:
        """创建函数节点"""
        return super().create_function(function)

    def create_variable(self, variable: VariableNode) -> bool:
        """创建变量节点"""
        return super().create_variable(variable)

    def create_project_contains_file(self, project_name: str, file_path: str) -> bool:
        """创建 Project-[:CONTAINS]->File 关系"""
        return super().create_project_contains_file(project_name, file_path)

    def create_file_defines_class(self, file_path: str, class_qualified_name: str) -> bool:
        """创建 File-[:DEFINES]->Class 关系"""
        return super().create_file_defines_class(file_path, class_qualified_name)

    def create_file_defines_function(self, file_path: str, function_qualified_name: str) -> bool:
        """创建 File-[:DEFINES]->Function 关系"""
        return super().create_file_defines_function(file_path, function_qualified_name)

    def create_class_has_method(self, class_qualified_name: str, method_qualified_name: str) -> bool:
        """创建 Class-[:HAS_METHOD]->Function 关系"""
        return super().create_class_has_method(class_qualified_name, method_qualified_name)

    def create_calls_relationship(self, call: CallRelationship) -> bool:
        """创建 Function-[:CALLS]->Function 关系"""
        return super().create_calls_relationship(call)

    def create_data_access_relationship(self, access: DataAccessRelationship) -> bool:
        """创建 Function-[:READS|:WRITES]->Variable 关系"""
        return super().create_data_access_relationship(access)

    def create_taint_flow_relationship(self, taint: TaintFlowRelationship) -> bool:
        """创建 Function-[:TAINT_FLOW_TO]->Function 关系"""
        return super().create_taint_flow_relationship(taint)

    def find_function_by_qualified_name(self, qualified_name: str) -> Optional[FunctionNode]:
        """根据全限定名查找函数节点"""
        self._ensure_connected()

        query = """
        MATCH (f:Function {qualified_name: $qualified_name})
        RETURN f
        LIMIT 1
        """

        try:
            with self._driver.session() as session:
                result = session.run(query, {"qualified_name": qualified_name})
                record = result.single()
                if record:
                    known_fields = {f.name for f in FunctionNode.__dataclass_fields__.values()}
                    node_data = {k: v for k, v in dict(record["f"]).items() if k in known_fields}
                    return FunctionNode(**node_data)
                return None
        except Exception as e:
            self.logger.error(f"Failed to find function by qualified name '{qualified_name}': {e}")
            raise GraphQueryException(f"Failed to find function: {e}")

    def find_taint_flows(self, source_function: Optional[str] = None,
                        sink_function: Optional[str] = None,
                        risk_level: Optional[str] = None, limit: int = 100) -> List[TaintFlowRelationship]:
        """查找污点流"""
        self._ensure_connected()

        conditions = []
        params: Dict[str, Any] = {"limit": limit}
        if source_function:
            conditions.append("src.qualified_name = $source_function")
            params["source_function"] = source_function
        if sink_function:
            conditions.append("snk.qualified_name = $sink_function")
            params["sink_function"] = sink_function
        if risk_level:
            conditions.append("r.risk = $risk_level")
            params["risk_level"] = risk_level

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
        MATCH (src:Function)-[r:TAINT_FLOW_TO]->(snk:Function)
        {where_clause}
        RETURN src.qualified_name AS source, snk.qualified_name AS sink,
               r.risk AS risk, r.vulnerability_type AS vulnerability_type,
               r.taint_path AS taint_path, r.description AS description
        LIMIT $limit
        """

        try:
            with self._driver.session() as session:
                result = session.run(query, params)
                flows = []
                for record in result:
                    flows.append(TaintFlowRelationship(
                        source_qualified_name=record["source"],
                        sink_qualified_name=record["sink"],
                        risk=record["risk"] or RiskLevel.HIGH,
                        vulnerability_type=record["vulnerability_type"],
                        taint_path=record["taint_path"],
                        description=record["description"],
                    ))
                return flows
        except Exception as e:
            self.logger.error(f"Failed to find taint flows: {e}")
            raise GraphQueryException(f"Failed to find taint flows: {e}")

    def get_subgraph_for_function(self, function_qualified_name: str, depth: int = 2) -> SubGraph:
        """获取函数子图（用于 LLM 上下文）"""
        self._ensure_connected()

        try:
            center_node_data = {}
            fn = self.find_function_by_qualified_name(function_qualified_name)
            if fn:
                center_node_data = {
                    "qualified_name": fn.qualified_name,
                    "name": fn.name,
                    "signature": fn.signature,
                    "body": fn.body,
                    "file_path": fn.file_path,
                }

            upstream = self.get_upstream_callers(function_qualified_name, depth)
            downstream = self.get_downstream_callees(function_qualified_name, depth)
            taint_flows = self.find_taint_flows(source_function=function_qualified_name)
            taint_data = [
                {"source": tf.source_qualified_name, "sink": tf.sink_qualified_name, "risk": tf.risk}
                for tf in taint_flows
            ]

            # 查找相关变量
            var_query = """
            MATCH (f:Function {qualified_name: $qualified_name})-[:READS|WRITES]->(v:Variable)
            RETURN DISTINCT v.qualified_name AS qualified_name, v.name AS name, v.var_type AS var_type
            """
            related_vars = []
            with self._driver.session() as session:
                result = session.run(var_query, {"qualified_name": function_qualified_name})
                for record in result:
                    related_vars.append(dict(record))

            return SubGraph(
                center_node=center_node_data,
                upstream_callers=upstream,
                downstream_callees=downstream,
                taint_flows=taint_data,
                related_variables=related_vars,
            )
        except Exception as e:
            self.logger.error(f"Failed to get subgraph for '{function_qualified_name}': {e}")
            raise GraphQueryException(f"Failed to get subgraph: {e}")

    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行原生 Cypher 查询"""
        self._ensure_connected()

        try:
            with self._driver.session() as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            self.logger.error(f"Failed to execute Cypher query: {e}")
            raise GraphQueryException(f"Failed to execute Cypher: {e}")

    # 子类必须实现的抽象方法
    def _create_node_impl(self, label, unique_key: str, properties: Dict[str, Any]) -> bool:
        """创建节点的具体实现"""
        self._ensure_connected()

        label_str = label.value if hasattr(label, 'value') else str(label)
        query = f"""
        MERGE (n:{label_str} {{{unique_key}: ${unique_key}}})
        SET n += $properties
        RETURN n
        """

        try:
            with self._driver.session() as session:
                parameters = {unique_key: properties.get(unique_key), "properties": properties}
                result = session.run(query, parameters)
                return result.single() is not None
        except Exception as e:
            self.logger.error(f"Failed to create node {label}: {e}")
            raise GraphQueryException(f"Failed to create node: {e}")

    def _create_relationship_impl(self,
                                 start_label, start_key: str, start_value: str,
                                 end_label, end_key: str, end_value: str,
                                 rel_type, properties: Dict[str, Any]) -> bool:
        """创建关系的具体实现"""
        self._ensure_connected()

        start_label_str = start_label.value if hasattr(start_label, 'value') else str(start_label)
        end_label_str = end_label.value if hasattr(end_label, 'value') else str(end_label)
        rel_type_str = rel_type.value if hasattr(rel_type, 'value') else str(rel_type)

        query = f"""
        MATCH (a:{start_label_str} {{{start_key}: ${start_key}}})
        MATCH (b:{end_label_str} {{{end_key}: ${end_key}}})
        MERGE (a)-[r:{rel_type_str}]->(b)
        SET r += $properties
        RETURN r
        """

        try:
            with self._driver.session() as session:
                parameters = {
                    start_key: start_value,
                    end_key: end_value,
                    "properties": properties
                }
                result = session.run(query, parameters)
                return result.single() is not None
        except Exception as e:
            self.logger.error(f"Failed to create relationship {rel_type}: {e}")
            raise GraphQueryException(f"Failed to create relationship: {e}")