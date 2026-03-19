from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class DistanceMetric(str, Enum):
    """向量距离度量类型"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    HAMMING = "hamming"


class IndexType(str, Enum):
    """索引类型"""
    FLAT = "flat"
    IVF_FLAT = "ivf_flat"
    IVF_SQ8 = "ivf_sq8"
    IVF_PQ = "ivf_pq"
    HNSW = "hnsw"


@dataclass
class VectorData:
    """向量数据模型"""
    id: Union[str, int]
    vector: List[float]
    payload: Optional[Dict[str, Any]] = None


@dataclass
class CollectionInfo:
    """集合信息"""
    name: str
    vector_size: int
    distance_metric: DistanceMetric
    vector_count: Optional[int] = None
    index_type: Optional[IndexType] = None
    description: Optional[str] = None


@dataclass
class SearchResult:
    """搜索结果"""
    id: Union[str, int]
    score: float
    vector: Optional[List[float]] = None
    payload: Optional[Dict[str, Any]] = None


@dataclass
class SearchParams:
    """搜索参数"""
    collection_name: str
    query_vector: List[float]
    limit: int = 10
    score_threshold: Optional[float] = None
    filter: Optional[Dict[str, Any]] = None
    with_vectors: bool = False
    offset: Optional[int] = None


@dataclass
class HybridSearchParams:
    """混合搜索参数"""
    collection_name: str
    dense_vector: List[float]
    sparse_vector: Optional[Dict[str, float]] = None
    text_query: Optional[str] = None
    limit: int = 10
    alpha: float = 0.5  # 稠密向量和稀疏向量的权重平衡
    score_threshold: Optional[float] = None
    filter: Optional[Dict[str, Any]] = None


@dataclass
class InsertParams:
    """插入参数"""
    collection_name: str
    data: List[VectorData]
    batch_size: Optional[int] = None


@dataclass
class DeleteParams:
    """删除参数"""
    collection_name: str
    ids: Optional[List[Union[str, int]]] = None
    filter: Optional[Dict[str, Any]] = None


@dataclass
class QueryParams:
    """查询参数"""
    collection_name: str
    filter: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    with_vectors: bool = False


@dataclass
class CollectionLimit:
    """集合限制信息"""
    max_collections: Optional[int] = None
    max_vectors_per_collection: Optional[int] = None
    max_vector_size: Optional[int] = None
    current_collections: Optional[int] = None
    current_vectors: Optional[int] = None