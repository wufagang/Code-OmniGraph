"""向量嵌入业务层领域模型定义"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class EmbeddingTarget(str, Enum):
    """嵌入对象类型"""
    FUNCTION = "function"   # 函数/方法源码
    CLASS = "class"         # 类文档/签名
    FILE = "file"           # 文件摘要


class CollectionName(str, Enum):
    """预定义集合名称"""
    FUNCTIONS = "code_functions"   # 函数源码向量集合
    CLASSES = "code_classes"       # 类向量集合


@dataclass
class MethodEmbedding:
    """方法嵌入数据，对应向量库中的一条记录"""
    qualified_name: str           # 全限定名，作为向量 ID
    vector: List[float]           # 嵌入向量
    name: Optional[str] = None
    signature: Optional[str] = None
    body: Optional[str] = None    # 方法源码（payload 原文）
    file_path: Optional[str] = None
    class_name: Optional[str] = None
    is_endpoint: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingSearchResult:
    """语义搜索结果"""
    qualified_name: str
    score: float                  # 相似度分数（越高越相似）
    name: Optional[str] = None
    signature: Optional[str] = None
    body: Optional[str] = None
    file_path: Optional[str] = None
    class_name: Optional[str] = None
    is_endpoint: bool = False


@dataclass
class EmbeddingStats:
    """嵌入向量库统计信息"""
    collection_name: str
    vector_count: int = 0
    vector_size: Optional[int] = None
