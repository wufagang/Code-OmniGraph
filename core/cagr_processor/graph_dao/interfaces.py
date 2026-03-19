"""图数据库接口定义（通用 DB 操作层，不含业务语义）"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class GraphDatabase(ABC):
    """图数据库通用接口，只定义底层 DB 操作契约，不含业务语义"""

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------

    @abstractmethod
    def connect(self) -> None:
        """建立数据库连接"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭数据库连接"""
        pass

    # ------------------------------------------------------------------
    # 事务管理
    # ------------------------------------------------------------------

    @abstractmethod
    def begin_transaction(self) -> Any:
        """开始事务，返回事务对象"""
        pass

    @abstractmethod
    def commit(self, tx: Any) -> None:
        """提交事务"""
        pass

    @abstractmethod
    def rollback(self, tx: Any) -> None:
        """回滚事务"""
        pass

    # ------------------------------------------------------------------
    # 通用节点操作
    # ------------------------------------------------------------------

    @abstractmethod
    def create_node(self, label: str, unique_key: str, properties: Dict[str, Any]) -> bool:
        """
        创建或更新节点（幂等，使用 MERGE 语义）

        Args:
            label: 节点标签，如 "Function"、"Class"
            unique_key: 用于 MERGE 匹配的唯一键字段名，如 "qualified_name"
            properties: 节点属性字典

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    def find_node(self, label: str, key: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        按单个字段查找节点，返回原始属性字典

        Args:
            label: 节点标签
            key: 匹配字段名
            value: 匹配字段值

        Returns:
            节点属性字典，未找到返回 None
        """
        pass

    @abstractmethod
    def find_nodes(self, label: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        按多个字段过滤查找节点列表，返回原始属性字典列表

        Args:
            label: 节点标签
            filters: 过滤条件字典，所有条件做 AND 匹配

        Returns:
            节点属性字典列表
        """
        pass

    # ------------------------------------------------------------------
    # 通用关系操作
    # ------------------------------------------------------------------

    @abstractmethod
    def create_relationship(
        self,
        start_label: str, start_key: str, start_value: str,
        end_label: str, end_key: str, end_value: str,
        rel_type: str, properties: Dict[str, Any]
    ) -> bool:
        """
        创建或更新关系（幂等，使用 MERGE 语义）

        Args:
            start_label: 起始节点标签
            start_key: 起始节点匹配字段名
            start_value: 起始节点匹配字段值
            end_label: 目标节点标签
            end_key: 目标节点匹配字段名
            end_value: 目标节点匹配字段值
            rel_type: 关系类型，如 "CALLS"、"DEFINES"
            properties: 关系属性字典

        Returns:
            操作是否成功
        """
        pass

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @abstractmethod
    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        执行原生查询语句（Neo4j 为 Cypher，其他后端自行适配）

        Args:
            query: 查询字符串
            parameters: 查询参数字典

        Returns:
            结果列表，每条结果为原始字典
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        获取图谱统计信息，返回原始字典

        Returns:
            统计字典，包含 total_nodes、total_relationships 等键
        """
        pass

    @abstractmethod
    def clear_graph(self) -> None:
        """清空整个图谱（谨慎使用）"""
        pass
