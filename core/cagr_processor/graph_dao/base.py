"""图数据库基础抽象类（仅保留 DB 层基础设施工具，不含业务逻辑）"""

import logging
from abc import ABC
from typing import List, Optional, Dict, Any
from functools import wraps
import time

from .interfaces import GraphDatabase
from .config import GraphDBConfig
from cagr_common.exceptions import (
    GraphDBException, GraphConnectionException, GraphTransactionException,
    GraphNodeException, GraphNodeNotFoundException, GraphRelationshipException, GraphQueryException
)


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器，仅对 GraphConnectionException 重试"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(self, *args, **kwargs)
                except GraphConnectionException as e:
                    if attempt < max_attempts - 1:
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.warning(
                                f"{func.__name__} failed on attempt {attempt + 1}, "
                                f"retrying in {delay} seconds..."
                            )
                        time.sleep(delay)
                    else:
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
                except Exception:
                    raise
        return wrapper
    return decorator


class BaseGraphDatabase(GraphDatabase, ABC):
    """图数据库基础抽象类，提供 DB 层基础设施工具方法"""

    def __init__(self, config: GraphDBConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._connection = None

    def _validate_connection(self):
        """验证连接状态，子类可重写以适配不同的连接对象"""
        if not self._connection:
            raise GraphConnectionException("Database connection is not established")

    def _format_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """格式化属性（处理 None 值和特殊类型），去除 None，保留空字符串"""
        formatted = {}
        for key, value in properties.items():
            if value is not None:
                if isinstance(value, (list, bool, int, float)):
                    formatted[key] = value
                elif isinstance(value, str):
                    formatted[key] = value
                else:
                    formatted[key] = str(value)
        return formatted

    def _batch_operation(self, items: List[Any], batch_size: int, operation_func) -> int:
        """批量操作辅助方法"""
        total_success = 0
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            try:
                success_count = operation_func(batch)
                total_success += success_count or 0
            except Exception as e:
                self.logger.error(f"Batch operation failed at offset {i}: {e}")
                raise
        return total_success

    def _log_operation(self, operation: str, **kwargs):
        """记录操作日志"""
        if self.config.enable_logging:
            self.logger.info(f"{operation} - params: {kwargs}")

    def _create_batch_nodes(self, nodes: List[Dict[str, Any]], label: str) -> int:
        """批量创建节点（使用 UNWIND Cypher）"""
        if not nodes:
            return 0
        query = f"""
        UNWIND $nodes AS node
        CREATE (n:{label})
        SET n = node
        RETURN count(n) as count
        """
        try:
            result = self.execute_cypher(query, {"nodes": nodes})
            return result[0]["count"] if result else 0
        except Exception as e:
            self.logger.error(f"Failed to batch create {label} nodes: {e}")
            raise

    def _create_batch_relationships(self, rels: List[Dict[str, Any]], rel_type: str) -> int:
        """批量创建关系（使用 UNWIND Cypher）"""
        if not rels:
            return 0
        query = f"""
        UNWIND $rels AS rel
        MATCH (a), (b)
        WHERE a.qualified_name = rel.start_node_id
          AND b.qualified_name = rel.end_node_id
        CREATE (a)-[r:{rel_type}]->(b)
        SET r = rel.properties
        RETURN count(r) as count
        """
        try:
            result = self.execute_cypher(query, {"rels": rels})
            return result[0]["count"] if result else 0
        except Exception as e:
            self.logger.error(f"Failed to batch create {rel_type} relationships: {e}")
            raise
