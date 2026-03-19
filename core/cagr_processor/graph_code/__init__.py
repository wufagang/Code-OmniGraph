"""
Code-OmniGraph 代码图谱业务层模块

包含领域模型和业务服务：
- models.py：图谱领域模型（节点、关系、枚举）
- graph_service.py：CodeGraphService 业务层服务
"""

from .models import (
    NodeLabel, RelType, RiskLevel,
    ProjectNode, FileNode, ClassNode, FunctionNode, VariableNode,
    CallRelationship, TaintFlowRelationship, DataAccessRelationship,
    GraphStats, SubGraph,
)
from .graph_service import CodeGraphService

__all__ = [
    # 枚举
    "NodeLabel", "RelType", "RiskLevel",
    # 节点模型
    "ProjectNode", "FileNode", "ClassNode", "FunctionNode", "VariableNode",
    # 关系模型
    "CallRelationship", "TaintFlowRelationship", "DataAccessRelationship",
    # 查询/结果模型
    "GraphStats", "SubGraph",
    # 业务服务
    "CodeGraphService",
]
