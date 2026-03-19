"""
统一的异常类定义模块
包含图数据库和向量数据库的所有异常类型
"""

from typing import Optional


# ==================== 图数据库异常 ====================

class GraphDBException(Exception):
    """图数据库基础异常"""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code


class GraphConnectionException(GraphDBException):
    """图数据库连接异常"""
    pass


class GraphTransactionException(GraphDBException):
    """图数据库事务异常"""
    pass


class GraphNodeException(GraphDBException):
    """图数据库节点操作异常"""

    def __init__(self, message: str, label: Optional[str] = None, code: Optional[str] = None):
        super().__init__(message, code)
        self.label = label


class GraphNodeNotFoundException(GraphNodeException):
    """图数据库节点不存在异常"""
    pass


class GraphRelationshipException(GraphDBException):
    """图数据库关系操作异常"""

    def __init__(self, message: str, rel_type: Optional[str] = None, code: Optional[str] = None):
        super().__init__(message, code)
        self.rel_type = rel_type


class GraphRelationshipNotFoundException(GraphRelationshipException):
    """图数据库关系不存在异常"""
    pass


class GraphQueryException(GraphDBException):
    """图数据库查询执行异常"""
    pass


class GraphConfigException(GraphDBException):
    """图数据库配置异常"""
    pass


class GraphSchemaException(GraphDBException):
    """图数据库Schema/约束操作异常"""
    pass


# ==================== 向量数据库异常 ====================

class VectorDBException(Exception):
    """向量数据库基础异常"""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code


class VectorConnectionException(VectorDBException):
    """向量数据库连接异常"""
    pass


class VectorCollectionException(VectorDBException):
    """向量数据库集合操作异常"""

    def __init__(self, message: str, collection_name: str, code: Optional[str] = None):
        super().__init__(message, code)
        self.collection_name = collection_name


class VectorCollectionNotFoundException(VectorCollectionException):
    """向量数据库集合不存在异常"""
    pass


class VectorCollectionAlreadyExistsException(VectorCollectionException):
    """向量数据库集合已存在异常"""
    pass


class VectorInsertException(VectorDBException):
    """向量数据库插入数据异常"""
    pass


class VectorSearchException(VectorDBException):
    """向量数据库搜索异常"""
    pass


class VectorDeleteException(VectorDBException):
    """向量数据库删除异常"""
    pass


class VectorQueryException(VectorDBException):
    """向量数据库查询异常"""
    pass


class VectorConfigException(VectorDBException):
    """向量数据库配置异常"""
    pass


# ==================== 嵌入模型异常 ====================

class EmbeddingException(Exception):
    """嵌入模型基础异常"""

    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.provider = provider


class EmbeddingConnectionException(EmbeddingException):
    """嵌入模型连接/网络异常（可重试）"""
    pass


class EmbeddingConfigException(EmbeddingException):
    """嵌入模型配置异常"""
    pass


class EmbeddingRateLimitException(EmbeddingException):
    """嵌入模型 API 限流异常"""
    pass


class EmbeddingTimeoutException(EmbeddingException):
    """嵌入模型请求超时异常"""
    pass