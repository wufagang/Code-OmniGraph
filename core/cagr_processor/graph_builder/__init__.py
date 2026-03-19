"""
Code-OmniGraph 图数据库模块

提供统一的图数据库接口，支持 Neo4j 及未来扩展的其他图数据库。
"""

from .interfaces import GraphDatabase
from .models import *
from .config import GraphDBConfig, Neo4jConfig
from cagr_common.exceptions import *
from .factory import GraphDBFactory
from .impl.neo4j_impl import Neo4jDatabase

# 便捷函数
def create_graph_db(config: GraphDBConfig = None) -> GraphDatabase:
    """创建图数据库实例"""
    if config is None:
        config = GraphDBConfig.from_env()
    return GraphDBFactory.create(config)

__all__ = [
    # 接口
    "GraphDatabase",
    # 模型
    "ProjectNode", "FileNode", "ClassNode", "FunctionNode", "VariableNode",
    "CallRelationship", "TaintFlowRelationship", "DataAccessRelationship",
    "GraphStats", "SubGraph", "NodeLabel", "RelType", "RiskLevel",
    # 配置
    "GraphDBConfig", "Neo4jConfig",
    # 异常
    "GraphDBException", "GraphConnectionException", "GraphTransactionException",
    "GraphNodeException", "GraphNodeNotFoundException", "GraphRelationshipException",
    "GraphQueryException", "GraphConfigException", "GraphSchemaException",
    # 工厂
    "GraphDBFactory",
    # 实现
    "Neo4jDatabase",
    # 便捷函数
    "create_graph_db"
]