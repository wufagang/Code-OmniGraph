"""Neo4j 图数据库实现（纯 DB 操作层，不含业务语义）"""

import logging
from typing import List, Optional, Dict, Any

try:
    from neo4j import GraphDatabase as Neo4jDriver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

from ..base import BaseGraphDatabase
from cagr_common.exceptions import (
    GraphConnectionException, GraphQueryException
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
    """Neo4j 图数据库实现，只实现通用 DB 操作接口"""

    def __init__(self, config):
        super().__init__(config)
        self._driver: Optional[Neo4jDriver] = None
        if not NEO4J_AVAILABLE:
            raise ImportError(
                "Neo4j driver is not installed. "
                "Please install it with: pip install neo4j"
            )

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------

    def connect(self):
        """连接到 Neo4j 数据库"""
        try:
            self._driver = Neo4jDriver.driver(
                self.config.neo4j_config.uri,
                auth=(self.config.neo4j_config.username, self.config.neo4j_config.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
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
        """重写基类验证方法，检查 Neo4j driver"""
        self._ensure_connected()

    # ------------------------------------------------------------------
    # 事务管理
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # 通用节点操作
    # ------------------------------------------------------------------

    def create_node(self, label, unique_key: str, properties: Dict[str, Any]) -> bool:
        """创建或更新节点（MERGE 语义，幂等）"""
        self._ensure_connected()

        label_str = label.value if hasattr(label, 'value') else str(label)
        query = f"""
        MERGE (n:{label_str} {{{unique_key}: ${unique_key}}})
        SET n += $properties
        RETURN n
        """

        try:
            with self._driver.session() as session:
                params = {unique_key: properties.get(unique_key), "properties": properties}
                result = session.run(query, params)
                return result.single() is not None
        except Exception as e:
            self.logger.error(f"Failed to create node {label_str}: {e}")
            raise GraphQueryException(f"Failed to create node: {e}")

    def find_node(self, label, key: str, value: Any) -> Optional[Dict[str, Any]]:
        """按单个字段查找节点，返回原始属性字典"""
        self._ensure_connected()

        label_str = label.value if hasattr(label, 'value') else str(label)
        query = f"""
        MATCH (n:{label_str} {{{key}: $value}})
        RETURN properties(n) AS props
        LIMIT 1
        """

        try:
            with self._driver.session() as session:
                result = session.run(query, {"value": value})
                record = result.single()
                return dict(record["props"]) if record else None
        except Exception as e:
            self.logger.error(f"Failed to find node {label_str} by {key}: {e}")
            raise GraphQueryException(f"Failed to find node: {e}")

    def find_nodes(self, label, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """按多个字段过滤查找节点列表，返回原始属性字典列表"""
        self._ensure_connected()

        label_str = label.value if hasattr(label, 'value') else str(label)
        if filters:
            conditions = " AND ".join(f"n.{k} = ${k}" for k in filters)
            query = f"MATCH (n:{label_str}) WHERE {conditions} RETURN properties(n) AS props"
        else:
            query = f"MATCH (n:{label_str}) RETURN properties(n) AS props"

        try:
            with self._driver.session() as session:
                result = session.run(query, filters)
                return [dict(record["props"]) for record in result]
        except Exception as e:
            self.logger.error(f"Failed to find nodes {label_str}: {e}")
            raise GraphQueryException(f"Failed to find nodes: {e}")

    # ------------------------------------------------------------------
    # 通用关系操作
    # ------------------------------------------------------------------

    def create_relationship(
        self,
        start_label, start_key: str, start_value: str,
        end_label, end_key: str, end_value: str,
        rel_type, properties: Dict[str, Any]
    ) -> bool:
        """创建或更新关系（MERGE 语义，幂等）"""
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
                params = {
                    start_key: start_value,
                    end_key: end_value,
                    "properties": properties
                }
                result = session.run(query, params)
                return result.single() is not None
        except Exception as e:
            self.logger.error(f"Failed to create relationship {rel_type_str}: {e}")
            raise GraphQueryException(f"Failed to create relationship: {e}")

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

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

    def get_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息，返回原始字典"""
        self._ensure_connected()

        queries = {
            "total_nodes": "MATCH (n) RETURN count(n) as count",
            "total_relationships": "MATCH ()-[r]->() RETURN count(r) as count",
            "projects": "MATCH (n:Project) RETURN count(n) as count",
            "files": "MATCH (n:File) RETURN count(n) as count",
            "classes": "MATCH (n:Class) RETURN count(n) as count",
            "functions": "MATCH (n:Function) RETURN count(n) as count",
            "variables": "MATCH (n:Variable) RETURN count(n) as count",
        }

        try:
            stats: Dict[str, Any] = {}
            with self._driver.session() as session:
                for key, query in queries.items():
                    result = session.run(query)
                    record = result.single()
                    stats[key] = record["count"] if record else 0
            return stats
        except Exception as e:
            self.logger.error(f"Failed to get graph stats: {e}")
            raise GraphQueryException(f"Failed to get graph stats: {e}")

    def clear_graph(self) -> None:
        """清空整个图谱（谨慎使用）"""
        self._ensure_connected()
        try:
            with self._driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            self.logger.warning("Graph has been cleared!")
        except Exception as e:
            self.logger.error(f"Failed to clear graph: {e}")
            raise GraphQueryException(f"Failed to clear graph: {e}")
