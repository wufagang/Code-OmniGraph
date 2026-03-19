"""
Code-OmniGraph 图数据库模块

提供统一的图数据库接口，支持 Neo4j 及未来扩展的其他图数据库。
"""

from .interfaces import GraphDatabase
from .config import GraphDBConfig, Neo4jConfig
from cagr_common.exceptions import *
from .factory import GraphDBFactory
from .impl.neo4j_impl import Neo4jDatabase
from cagr_processor.graph_code.models import *

# 业务层（通过 graph_dao 统一导出，方便调用方使用）
from cagr_processor.graph_code.graph_service import CodeGraphService

# 便捷函数
def create_graph_db(config: GraphDBConfig = None) -> GraphDatabase:
    """创建图数据库实例（DB 层）"""
    if config is None:
        config = GraphDBConfig.from_env()
    return GraphDBFactory.create(config)

def create_graph_service(config: GraphDBConfig = None) -> CodeGraphService:
    """创建代码图谱业务服务实例（业务层）"""
    db = create_graph_db(config)
    return CodeGraphService(db)

__all__ = [
    # DB 层接口
    "GraphDatabase",
    # 业务层服务
    "CodeGraphService",
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
    "create_graph_db",
    "create_graph_service",
]