"""图数据库接口定义"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union

from .models import (
    ProjectNode, FileNode, ClassNode, FunctionNode, VariableNode,
    CallRelationship, TaintFlowRelationship, DataAccessRelationship,
    GraphStats, SubGraph, NodeLabel, RelType
)


class GraphDatabase(ABC):
    """图数据库接口定义"""

    @abstractmethod
    def connect(self) -> None:
        """建立数据库连接"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭数据库连接"""
        pass

    @abstractmethod
    def begin_transaction(self) -> Any:
        """开始事务"""
        pass

    @abstractmethod
    def commit(self, tx: Any) -> None:
        """提交事务"""
        pass

    @abstractmethod
    def rollback(self, tx: Any) -> None:
        """回滚事务"""
        pass

    @abstractmethod
    def create_project(self, project: ProjectNode) -> bool:
        """创建项目节点"""
        pass

    @abstractmethod
    def create_file(self, file: FileNode) -> bool:
        """创建文件节点"""
        pass

    @abstractmethod
    def create_class(self, class_node: ClassNode) -> bool:
        """创建类节点"""
        pass

    @abstractmethod
    def create_function(self, function: FunctionNode) -> bool:
        """创建函数节点"""
        pass

    @abstractmethod
    def create_variable(self, variable: VariableNode) -> bool:
        """创建变量节点"""
        pass

    @abstractmethod
    def create_project_contains_file(self, project_name: str, file_path: str) -> bool:
        """创建 Project-[:CONTAINS]->File 关系"""
        pass

    @abstractmethod
    def create_file_defines_class(self, file_path: str, class_qualified_name: str) -> bool:
        """创建 File-[:DEFINES]->Class 关系"""
        pass

    @abstractmethod
    def create_file_defines_function(self, file_path: str, function_qualified_name: str) -> bool:
        """创建 File-[:DEFINES]->Function 关系"""
        pass

    @abstractmethod
    def create_class_has_method(self, class_qualified_name: str, method_qualified_name: str) -> bool:
        """创建 Class-[:HAS_METHOD]->Function 关系"""
        pass

    @abstractmethod
    def create_calls_relationship(self, call: CallRelationship) -> bool:
        """创建 Function-[:CALLS]->Function 关系"""
        pass

    @abstractmethod
    def create_data_access_relationship(self, access: DataAccessRelationship) -> bool:
        """创建 Function-[:READS|:WRITES]->Variable 关系"""
        pass

    @abstractmethod
    def create_taint_flow_relationship(self, taint: TaintFlowRelationship) -> bool:
        """创建 Function-[:TAINT_FLOW_TO]->Function 关系（Joern 注入）"""
        pass

    @abstractmethod
    def find_function_by_name(self, name: str) -> Optional[FunctionNode]:
        """根据函数名查找函数节点"""
        pass

    @abstractmethod
    def find_function_by_qualified_name(self, qualified_name: str) -> Optional[FunctionNode]:
        """根据全限定名查找函数节点"""
        pass

    @abstractmethod
    def get_call_chain(self, function_qualified_name: str, depth: int = 3) -> List[Dict[str, Any]]:
        """获取函数调用链"""
        pass

    @abstractmethod
    def get_upstream_callers(self, function_qualified_name: str, depth: int = 1) -> List[Dict[str, Any]]:
        """获取上游调用者"""
        pass

    @abstractmethod
    def get_downstream_callees(self, function_qualified_name: str, depth: int = 1) -> List[Dict[str, Any]]:
        """获取下游被调用者"""
        pass

    @abstractmethod
    def find_taint_flows(self, source_function: Optional[str] = None, sink_function: Optional[str] = None,
                        risk_level: Optional[str] = None, limit: int = 100) -> List[TaintFlowRelationship]:
        """查找污点流"""
        pass

    @abstractmethod
    def find_vulnerable_paths(self, sink_function_name: str) -> List[List[Dict[str, Any]]]:
        """查找到达危险函数（sink）的所有路径"""
        pass

    @abstractmethod
    def get_subgraph_for_function(self, function_qualified_name: str, depth: int = 2) -> SubGraph:
        """获取函数子图（用于 LLM 上下文）"""
        pass

    @abstractmethod
    def get_graph_stats(self) -> GraphStats:
        """获取图谱统计信息"""
        pass

    @abstractmethod
    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行原生 Cypher 查询"""
        pass

    @abstractmethod
    def clear_graph(self) -> None:
        """清空整个图谱（谨慎使用）"""
        pass
