"""
向量数据库模块

提供统一的接口支持多种向量数据库，包括Qdrant和Milvus。
"""

# 导出主要接口和类
from .interfaces import VectorDatabase
from .config import VectorDBConfig, QdrantConfig, MilvusConfig
from .factory import VectorDBFactory
from .models import (
    VectorData, CollectionInfo, SearchResult, SearchParams,
    HybridSearchParams, CollectionLimit, DistanceMetric, IndexType,
    InsertParams, DeleteParams, QueryParams
)
from cagr_common.exceptions import (
    VectorDBException, VectorConnectionException, VectorCollectionException,
    VectorCollectionNotFoundException, VectorCollectionAlreadyExistsException,
    VectorInsertException, VectorSearchException, VectorDeleteException, VectorQueryException,
    VectorConfigException
)

# 导出实现类（可选）
from .impl.qdrant_impl import QdrantDatabase
from .impl.milvus_impl import MilvusDatabase

__all__ = [
    # 主要接口
    "VectorDatabase",
    "VectorDBConfig",
    "QdrantConfig",
    "MilvusConfig",
    "VectorDBFactory",

    # 数据模型
    "VectorData",
    "CollectionInfo",
    "SearchResult",
    "SearchParams",
    "HybridSearchParams",
    "CollectionLimit",
    "DistanceMetric",
    "IndexType",
    "InsertParams",
    "DeleteParams",
    "QueryParams",

    # 异常类
    "VectorDBException",
    "VectorConnectionException",
    "VectorCollectionException",
    "VectorCollectionNotFoundException",
    "VectorCollectionAlreadyExistsException",
    "VectorInsertException",
    "VectorSearchException",
    "VectorDeleteException",
    "VectorQueryException",
    "VectorConfigException",

    # 实现类
    "QdrantDatabase",
    "MilvusDatabase",

    # 工厂方法
    "create_vector_db",
]


def create_vector_db(
    db_type: str = "qdrant",
    **kwargs
) -> VectorDatabase:
    """
    快速创建向量数据库实例的便捷函数

    Args:
        db_type: 数据库类型 ('qdrant' 或 'milvus')
        **kwargs: 配置参数

    Returns:
        向量数据库实例

    Example:
        # 创建Qdrant实例
        db = create_vector_db("qdrant", host="localhost", port=6333)

        # 创建Milvus实例
        db = create_vector_db("milvus", host="localhost", port=19530)

        # 从环境变量创建
        db = create_vector_db()
    """
    if not kwargs:
        # 如果没有提供参数，从环境变量加载
        return VectorDBFactory.create_from_env()

    # 构建配置字典
    config_dict = {"db_type": db_type}

    if db_type == "qdrant":
        qdrant_config = {}
        if "host" in kwargs:
            qdrant_config["host"] = kwargs.pop("host")
        if "port" in kwargs:
            qdrant_config["port"] = kwargs.pop("port")
        if "url" in kwargs:
            qdrant_config["url"] = kwargs.pop("url")
        if "api_key" in kwargs:
            qdrant_config["api_key"] = kwargs.pop("api_key")

        config_dict["qdrant_config"] = qdrant_config

    elif db_type == "milvus":
        milvus_config = {}
        if "host" in kwargs:
            milvus_config["host"] = kwargs.pop("host")
        if "port" in kwargs:
            milvus_config["port"] = kwargs.pop("port")
        if "uri" in kwargs:
            milvus_config["uri"] = kwargs.pop("uri")
        if "user" in kwargs:
            milvus_config["user"] = kwargs.pop("user")
        if "password" in kwargs:
            milvus_config["password"] = kwargs.pop("password")

        config_dict["milvus_config"] = milvus_config

    # 添加其他通用配置
    config_dict.update(kwargs)

    return VectorDBFactory.create_from_config_dict(config_dict)