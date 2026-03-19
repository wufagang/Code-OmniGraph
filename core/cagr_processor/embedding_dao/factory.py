"""向量数据库工厂类"""

from typing import Dict, Type, Optional
import logging

from .interfaces import VectorDatabase
from .config import VectorDBConfig, QdrantConfig, MilvusConfig
from .impl.qdrant_impl import QdrantDatabase
from .impl.milvus_impl import MilvusDatabase
from cagr_common.exceptions import VectorConfigException


class VectorDBFactory:
    """向量数据库工厂类"""

    # 注册的数据库实现
    _registry: Dict[str, Type[VectorDatabase]] = {
        "qdrant": QdrantDatabase,
        "milvus": MilvusDatabase,
    }

    @classmethod
    def register(cls, db_type: str, implementation: Type[VectorDatabase]):
        """注册新的数据库实现"""
        cls._registry[db_type.lower()] = implementation

    @classmethod
    def create(cls, config: VectorDBConfig) -> VectorDatabase:
        """
        创建向量数据库实例

        Args:
            config: 数据库配置

        Returns:
            向量数据库实例

        Raises:
            VectorConfigException: 配置错误
        """
        try:
            # 验证配置
            config.validate()

            # 获取数据库类型
            db_type = config.db_type.lower()

            # 检查是否支持该类型
            if db_type not in cls._registry:
                supported_types = list(cls._registry.keys())
                raise VectorConfigException(
                    f"Unsupported vector database type: {db_type}. "
                    f"Supported types: {supported_types}"
                )

            # 获取实现类
            implementation_class = cls._registry[db_type]

            # 创建实例
            try:
                instance = implementation_class(config)
            except ImportError as e:
                # 处理导入错误，提供更有用的错误信息
                if "qdrant-client" in str(e):
                    raise VectorConfigException(
                        "Qdrant client library is not installed. "
                        "Please install it with: pip install qdrant-client"
                    )
                elif "pymilvus" in str(e):
                    raise VectorConfigException(
                        "Milvus client library is not installed. "
                        "Please install it with: pip install pymilvus"
                    )
                else:
                    raise VectorConfigException(f"Failed to import required library: {e}")

            logging.info(f"Successfully created {db_type} vector database instance")
            return instance

        except VectorConfigException:
            raise
        except Exception as e:
            raise VectorConfigException(f"Failed to create vector database instance: {e}")

    @classmethod
    def create_from_config_dict(cls, config_dict: dict) -> VectorDatabase:
        """
        从配置字典创建实例

        Args:
            config_dict: 配置字典

        Returns:
            向量数据库实例
        """
        try:
            db_type = config_dict.get("db_type", "qdrant").lower()

            if db_type == "qdrant":
                qdrant_config = QdrantConfig(**config_dict.get("qdrant_config", {}))
                config = VectorDBConfig(
                    db_type=db_type,
                    qdrant_config=qdrant_config,
                    **{k: v for k, v in config_dict.items() if k not in ["db_type", "qdrant_config"]}
                )
            elif db_type == "milvus":
                milvus_config = MilvusConfig(**config_dict.get("milvus_config", {}))
                config = VectorDBConfig(
                    db_type=db_type,
                    milvus_config=milvus_config,
                    **{k: v for k, v in config_dict.items() if k not in ["db_type", "milvus_config"]}
                )
            else:
                raise VectorConfigException(f"Unsupported db_type: {db_type}")

            return cls.create(config)

        except Exception as e:
            raise VectorConfigException(f"Failed to create instance from config dict: {e}")

    @classmethod
    def create_from_env(cls) -> VectorDatabase:
        """
        从环境变量创建实例

        Returns:
            向量数据库实例
        """
        config = VectorDBConfig.from_env()
        return cls.create(config)

    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的数据库类型列表"""
        return list(cls._registry.keys())

    @classmethod
    def is_supported(cls, db_type: str) -> bool:
        """检查是否支持指定的数据库类型"""
        return db_type.lower() in cls._registry