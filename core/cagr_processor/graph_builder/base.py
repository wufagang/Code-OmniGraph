"""图数据库基础抽象类"""

import logging
from abc import ABC
from typing import List, Optional, Dict, Any, Union
from functools import wraps
import time

from .interfaces import GraphDatabase
from .models import (
    ProjectNode, FileNode, ClassNode, FunctionNode, VariableNode,
    CallRelationship, TaintFlowRelationship, DataAccessRelationship,
    GraphStats, SubGraph, NodeLabel, RelType, RiskLevel
)
from .config import GraphDBConfig
from .exceptions import (
    GraphDBException, ConnectionException, TransactionException,
    NodeException, NodeNotFoundException, RelationshipException, QueryException
)


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(self, *args, **kwargs)
                except ConnectionException as e:
                    last_exception = e
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
                except Exception as e:
                    # 非连接异常不重试
                    raise
            raise last_exception
        return wrapper
    return decorator


class BaseGraphDatabase(GraphDatabase, ABC):
    """图数据库基础抽象类"""

    def __init__(self, config: GraphDBConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._connection = None
        self._transaction_stack = []  # 事务栈

    def _validate_connection(self):
        """验证连接状态"""
        if not self._connection:
            raise ConnectionException("Database connection is not established")

    def _validate_node_data(self, node_data: Dict[str, Any], required_fields: List[str]):
        """验证节点数据"""
        missing_fields = [f for f in required_fields if f not in node_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

    def _format_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """格式化属性（处理 None 值和特殊类型）"""
        formatted = {}
        for key, value in properties.items():
            if value is not None:
                # 处理列表类型
                if isinstance(value, list):
                    formatted[key] = value
                # 处理布尔类型
                elif isinstance(value, bool):
                    formatted[key] = value
                # 处理数字类型
                elif isinstance(value, (int, float)):
                    formatted[key] = value
                # 处理字符串类型
                elif isinstance(value, str):
                    # 去除空字符串
                    if value:
                        formatted[key] = value
                # 其他类型转换为字符串
                else:
                    formatted[key] = str(value)
        return formatted

    def _batch_operation(self, items: List[Any], batch_size: int, operation_func):
        """批量操作辅助方法"""
        total_success = 0

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            try:
                success_count = operation_func(batch)
                total_success += success_count
            except Exception as e:
                self.logger.error(f"Batch operation failed at offset {i}: {e}")
                raise

        return total_success

    def _log_operation(self, operation: str, **kwargs):
        """记录操作日志"""
        if self.config.enable_logging:
            self.logger.info(f"{operation} - params: {kwargs}")

    def _create_batch_nodes(self, nodes: List[Dict[str, Any]], label: str) -> int:
        """批量创建节点"""
        if not nodes:
            return 0

        # 使用 UNWIND 批量写入
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
        """批量创建关系"""
        if not rels:
            return 0

        # 使用 UNWIND 批量写入
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

    # 基础实现，子类可以重写
    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_project(self, project: ProjectNode) -> bool:
        """创建项目节点的基础实现"""
        self._validate_connection()
        self._log_operation("create_project", name=project.name)

        properties = self._format_properties({
            "name": project.name,
            "version": project.version,
            "language": project.language,
            "path": project.path,
            **project.metadata
        })

        return self._create_node_impl(NodeLabel.PROJECT, project.name, properties)

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_file(self, file: FileNode) -> bool:
        """创建文件节点的基础实现"""
        self._validate_connection()
        self._log_operation("create_file", path=file.path)

        properties = self._format_properties({
            "path": file.path,
            "name": file.name,
            "language": file.language,
            "content": file.content,
            "size": file.size,
            **file.metadata
        })

        return self._create_node_impl(NodeLabel.FILE, file.path, properties)

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_class(self, class_node: ClassNode) -> bool:
        """创建类节点的基础实现"""
        self._validate_connection()
        self._log_operation("create_class", qualified_name=class_node.qualified_name)

        properties = self._format_properties({
            "qualified_name": class_node.qualified_name,
            "name": class_node.name,
            "file_path": class_node.file_path,
            "docstring": class_node.docstring,
            "is_interface": class_node.is_interface,
            "is_abstract": class_node.is_abstract,
            "start_line": class_node.start_line,
            "end_line": class_node.end_line,
            **class_node.metadata
        })

        return self._create_node_impl(NodeLabel.CLASS, class_node.qualified_name, properties)

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_function(self, function: FunctionNode) -> bool:
        """创建函数节点的基础实现"""
        self._validate_connection()
        self._log_operation("create_function", qualified_name=function.qualified_name)

        properties = self._format_properties({
            "qualified_name": function.qualified_name,
            "name": function.name,
            "signature": function.signature,
            "body": function.body,
            "file_path": function.file_path,
            "class_name": function.class_name,
            "return_type": function.return_type,
            "start_line": function.start_line,
            "end_line": function.end_line,
            "is_endpoint": function.is_endpoint,
            "is_constructor": function.is_constructor,
            "docstring": function.docstring,
            **function.metadata
        })

        return self._create_node_impl(NodeLabel.FUNCTION, function.qualified_name, properties)

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_variable(self, variable: VariableNode) -> bool:
        """创建变量节点的基础实现"""
        self._validate_connection()
        self._log_operation("create_variable", qualified_name=variable.qualified_name)

        properties = self._format_properties({
            "qualified_name": variable.qualified_name,
            "name": variable.name,
            "var_type": variable.var_type,
            "file_path": variable.file_path,
            "class_name": variable.class_name,
            **variable.metadata
        })

        return self._create_node_impl(NodeLabel.VARIABLE, variable.qualified_name, properties)

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_project_contains_file(self, project_name: str, file_path: str) -> bool:
        """创建 Project-[:CONTAINS]->File 关系的基础实现"""
        self._validate_connection()
        self._log_operation("create_project_contains_file", project=project_name, file=file_path)

        return self._create_relationship_impl(
            NodeLabel.PROJECT, "name", project_name,
            NodeLabel.FILE, "path", file_path,
            RelType.CONTAINS, {}
        )

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_file_defines_class(self, file_path: str, class_qualified_name: str) -> bool:
        """创建 File-[:DEFINES]->Class 关系的基础实现"""
        self._validate_connection()
        self._log_operation("create_file_defines_class", file=file_path, class_=class_qualified_name)

        return self._create_relationship_impl(
            NodeLabel.FILE, "path", file_path,
            NodeLabel.CLASS, "qualified_name", class_qualified_name,
            RelType.DEFINES, {}
        )

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_file_defines_function(self, file_path: str, function_qualified_name: str) -> bool:
        """创建 File-[:DEFINES]->Function 关系的基础实现"""
        self._validate_connection()
        self._log_operation("create_file_defines_function", file=file_path, function=function_qualified_name)

        return self._create_relationship_impl(
            NodeLabel.FILE, "path", file_path,
            NodeLabel.FUNCTION, "qualified_name", function_qualified_name,
            RelType.DEFINES, {}
        )

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_class_has_method(self, class_qualified_name: str, method_qualified_name: str) -> bool:
        """创建 Class-[:HAS_METHOD]->Function 关系的基础实现"""
        self._validate_connection()
        self._log_operation("create_class_has_method", class_=class_qualified_name, method=method_qualified_name)

        return self._create_relationship_impl(
            NodeLabel.CLASS, "qualified_name", class_qualified_name,
            NodeLabel.FUNCTION, "qualified_name", method_qualified_name,
            RelType.HAS_METHOD, {}
        )

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_calls_relationship(self, call: CallRelationship) -> bool:
        """创建 Function-[:CALLS]->Function 关系的基础实现"""
        self._validate_connection()
        self._log_operation("create_calls_relationship",
                          caller=call.caller_qualified_name,
                          callee=call.callee_qualified_name)

        properties = self._format_properties({
            "call_site_line": call.call_site_line,
            **call.metadata
        })

        return self._create_relationship_impl(
            NodeLabel.FUNCTION, "qualified_name", call.caller_qualified_name,
            NodeLabel.FUNCTION, "qualified_name", call.callee_qualified_name,
            RelType.CALLS, properties
        )

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_data_access_relationship(self, access: DataAccessRelationship) -> bool:
        """创建 Function-[:READS|:WRITES]->Variable 关系的基础实现"""
        self._validate_connection()
        self._log_operation("create_data_access_relationship",
                          function=access.function_qualified_name,
                          variable=access.variable_qualified_name,
                          access_type=access.access_type)

        properties = self._format_properties({
            "line": access.line,
            **access.metadata
        })

        rel_type = RelType.READS if access.access_type.upper() == "READ" else RelType.WRITES

        return self._create_relationship_impl(
            NodeLabel.FUNCTION, "qualified_name", access.function_qualified_name,
            NodeLabel.VARIABLE, "qualified_name", access.variable_qualified_name,
            rel_type, properties
        )

    @retry_on_failure(max_attempts=3, delay=1.0)
    def create_taint_flow_relationship(self, taint: TaintFlowRelationship) -> bool:
        """创建 Function-[:TAINT_FLOW_TO]->Function 关系的基础实现"""
        self._validate_connection()
        self._log_operation("create_taint_flow_relationship",
                          source=taint.source_qualified_name,
                          sink=taint.sink_qualified_name,
                          risk=taint.risk)

        properties = self._format_properties({
            "risk": taint.risk,
            "vulnerability_type": taint.vulnerability_type,
            "taint_path": taint.taint_path,
            "description": taint.description,
            **taint.metadata
        })

        return self._create_relationship_impl(
            NodeLabel.FUNCTION, "qualified_name", taint.source_qualified_name,
            NodeLabel.FUNCTION, "qualified_name", taint.sink_qualified_name,
            RelType.TAINT_FLOW_TO, properties
        )

    # 子类必须实现的抽象方法
    def _create_node_impl(self, label: str, unique_key: str, properties: Dict[str, Any]) -> bool:
        """子类实现具体的节点创建逻辑"""
        raise NotImplementedError

    def _create_relationship_impl(self,
                                 start_label: str, start_key: str, start_value: str,
                                 end_label: str, end_key: str, end_value: str,
                                 rel_type: str, properties: Dict[str, Any]) -> bool:
        """子类实现具体的关系创建逻辑"""
        raise NotImplementedError
