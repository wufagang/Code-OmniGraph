"""图数据库异常类定义"""

from typing import Optional


class GraphDBException(Exception):
    """图数据库基础异常"""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code


class ConnectionException(GraphDBException):
    """连接异常"""
    pass


class TransactionException(GraphDBException):
    """事务异常"""
    pass


class NodeException(GraphDBException):
    """节点操作异常"""

    def __init__(self, message: str, label: Optional[str] = None, code: Optional[str] = None):
        super().__init__(message, code)
        self.label = label


class NodeNotFoundException(NodeException):
    """节点不存在异常"""
    pass


class RelationshipException(GraphDBException):
    """关系操作异常"""

    def __init__(self, message: str, rel_type: Optional[str] = None, code: Optional[str] = None):
        super().__init__(message, code)
        self.rel_type = rel_type


class QueryException(GraphDBException):
    """查询执行异常"""
    pass


class ConfigException(GraphDBException):
    """配置异常"""
    pass


class SchemaException(GraphDBException):
    """Schema/约束操作异常"""
    pass
