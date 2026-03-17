from typing import Optional

"""向量数据库异常类定义"""


class VectorDBException(Exception):
    """向量数据库基础异常"""
    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code


class ConnectionException(VectorDBException):
    """连接异常"""
    pass


class CollectionException(VectorDBException):
    """集合操作异常"""
    def __init__(self, message: str, collection_name: str, code: Optional[str] = None):
        super().__init__(message, code)
        self.collection_name = collection_name


class CollectionNotFoundException(CollectionException):
    """集合不存在异常"""
    pass


class CollectionAlreadyExistsException(CollectionException):
    """集合已存在异常"""
    pass


class InsertException(VectorDBException):
    """插入数据异常"""
    pass


class SearchException(VectorDBException):
    """搜索异常"""
    pass


class DeleteException(VectorDBException):
    """删除异常"""
    pass


class QueryException(VectorDBException):
    """查询异常"""
    pass


class ConfigException(VectorDBException):
    """配置异常"""
    pass