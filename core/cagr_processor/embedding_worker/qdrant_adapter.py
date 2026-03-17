"""
QdrantWorker适配器
为保持向后兼容性，提供与原有QdrantWorker相同的接口
"""

from typing import List
import sys
import os

# 添加路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from cagr_common.models import Method

from . import create_vector_db, VectorData


class QdrantWorker:
    """
    QdrantWorker适配器类

    保持与原有QdrantWorker相同的接口，但内部使用新的向量数据库框架
    """

    def __init__(self, url: str):
        """
        初始化QdrantWorker

        Args:
            url: Qdrant服务URL
        """
        # 使用新的工厂方法创建Qdrant实例
        self.db = create_vector_db("qdrant", url=url)
        self.collection_name = "methods"

        # 确保集合存在
        if not self.db.has_collection(self.collection_name):
            self.db.create_collection(
                collection_name=self.collection_name,
                vector_size=768,
                distance_metric="cosine"
            )

    def embed_and_upsert(self, methods: List[Method]):
        """
        嵌入并向量存储方法数据

        保持与原有接口一致，但内部使用新的实现

        Args:
            methods: Method对象列表
        """
        # 转换数据格式
        vector_data = []
        for i, method in enumerate(methods):
            # 使用虚拟向量（保持与原有实现一致）
            dummy_vector = [0.1] * 768

            vector_data.append(VectorData(
                id=str(i),  # 使用字符串ID
                vector=dummy_vector,
                payload={
                    "method_id": method.id,
                    "name": method.name,
                    "class": method.class_name
                }
            ))

        # 使用新的插入方法
        self.db.insert(
            collection_name=self.collection_name,
            data=vector_data
        )

    def __enter__(self):
        """上下文管理器支持"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self.db:
            self.db.close()