"""图数据库领域模型定义"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class NodeLabel(str, Enum):
    """图谱节点标签"""
    PROJECT = "Project"
    FILE = "File"
    CLASS = "Class"
    FUNCTION = "Function"     # 通用函数/方法，用 Function 统一
    VARIABLE = "Variable"


class RelType(str, Enum):
    """图谱关系类型"""
    # 结构关系
    CONTAINS = "CONTAINS"           # Project -> File
    DEFINES = "DEFINES"             # File -> Class|Function
    HAS_METHOD = "HAS_METHOD"       # Class -> Function
    # 调用关系
    CALLS = "CALLS"                 # Function -> Function
    # 数据访问
    READS = "READS"                 # Function -> Variable
    WRITES = "WRITES"               # Function -> Variable
    # 安全：污点流
    TAINT_FLOW_TO = "TAINT_FLOW_TO" # Function -> Function (Joern 注入)
    # 继承/实现
    INHERITS = "INHERITS"           # Class -> Class
    IMPLEMENTS = "IMPLEMENTS"       # Class -> Class (interface)


class RiskLevel(str, Enum):
    """污点流风险等级"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"


@dataclass
class ProjectNode:
    """项目节点"""
    name: str
    version: Optional[str] = None
    language: Optional[str] = None
    path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileNode:
    """文件节点"""
    path: str                         # 相对于项目根目录的路径（作为唯一键）
    name: str
    language: Optional[str] = None
    content: Optional[str] = None    # 文件原始内容（方便 LLM 读取）
    size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassNode:
    """类节点"""
    qualified_name: str               # 全限定名，作为唯一键
    name: str
    file_path: Optional[str] = None  # 归属文件
    docstring: Optional[str] = None
    is_interface: bool = False
    is_abstract: bool = False
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FunctionNode:
    """函数/方法节点"""
    qualified_name: str               # 全限定名，作为唯一键（e.g. com.example.Foo#bar）
    name: str
    signature: Optional[str] = None
    body: Optional[str] = None       # 方法源码（LLM 上下文的核心载体）
    file_path: Optional[str] = None
    class_name: Optional[str] = None  # 归属类的全限定名
    return_type: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    is_endpoint: bool = False          # 是否为 API 入口（如 @app.route / @GetMapping）
    is_constructor: bool = False
    docstring: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VariableNode:
    """变量节点"""
    qualified_name: str               # 唯一键
    name: str
    var_type: Optional[str] = None
    file_path: Optional[str] = None
    class_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallRelationship:
    """函数调用关系"""
    caller_qualified_name: str
    callee_qualified_name: str
    call_site_line: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaintFlowRelationship:
    """污点流关系（由 Joern 微观分析注入）"""
    source_qualified_name: str
    sink_qualified_name: str
    risk: RiskLevel = RiskLevel.HIGH
    vulnerability_type: Optional[str] = None   # e.g. "SQL_INJECTION", "COMMAND_INJECTION"
    taint_path: Optional[List[str]] = None     # 中间经过的节点路径
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataAccessRelationship:
    """数据访问关系（读/写变量）"""
    function_qualified_name: str
    variable_qualified_name: str
    access_type: str                   # "READS" | "WRITES"
    line: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphStats:
    """图谱统计信息"""
    node_counts: Dict[str, int] = field(default_factory=dict)
    relationship_counts: Dict[str, int] = field(default_factory=dict)
    total_nodes: int = 0
    total_relationships: int = 0


@dataclass
class SubGraph:
    """子图（用于 LLM 上下文组装）"""
    center_node: Dict[str, Any]
    upstream_callers: List[Dict[str, Any]] = field(default_factory=list)
    downstream_callees: List[Dict[str, Any]] = field(default_factory=list)
    taint_flows: List[Dict[str, Any]] = field(default_factory=list)
    related_variables: List[Dict[str, Any]] = field(default_factory=list)
