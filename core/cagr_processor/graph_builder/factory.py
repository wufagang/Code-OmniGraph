"""图数据库工厂类"""

from typing import Dict, Type, Optional
import logging

from .interfaces import GraphDatabase
from .config import GraphDBConfig, Neo4jConfig
from .impl.neo4j_impl import Neo4jDatabase
from cagr_common.exceptions import GraphConfigException


class GraphDBFactory:
    """图数据库工厂类"""

    # 注册的数据库实现
    _registry: Dict[str, Type[GraphDatabase]] = {
        "neo4j": Neo4jDatabase,
    }

    @classmethod
    def register(cls, db_type: str, implementation: Type[GraphDatabase]):
        """注册新的数据库实现"""
        cls._registry[db_type.lower()] = implementation

    @classmethod
    def create(cls, config: GraphDBConfig) -> GraphDatabase:
        """
        创建图数据库实例

        Args:
            config: 数据库配置

        Returns:
            图数据库实例

        Raises:
            ConfigException: 配置错误
        """
        try:
            # 验证配置
            config.validate()

            # 获取数据库类型
            db_type = config.db_type.lower()

            # 检查是否支持该类型
            if db_type not in cls._registry:
                supported_types = list(cls._registry.keys())
                raise GraphConfigException(
                    f"Unsupported graph database type: {db_type}. "
                    f"Supported types: {supported_types}"
                )

            # 获取实现类
            implementation_class = cls._registry[db_type]

            # 创建实例
            try:
                instance = implementation_class(config)
                instance.connect()
            except ImportError as e:
                # 处理导入错误，提供更有用的错误信息
                if "neo4j" in str(e):
                    raise GraphConfigException(
                        "Neo4j driver is not installed. "
                        "Please install it with: pip install neo4j"
                    )
                else:
                    raise GraphConfigException(f"Failed to import required library: {e}")

            logging.info(f"Successfully created {db_type} graph database instance")
            return instance

        except GraphConfigException:
            raise
        except Exception as e:
            raise GraphConfigException(f"Failed to create graph database instance: {e}")

    @classmethod
    def create_from_config_dict(cls, config_dict: dict) -> GraphDatabase:
        """
        从配置字典创建实例

        Args:
            config_dict: 配置字典

        Returns:
            图数据库实例
        """
        try:
            db_type = config_dict.get("db_type", "neo4j").lower()

            if db_type == "neo4j":
                neo4j_config = Neo4jConfig(**config_dict.get("neo4j_config", {}))
                config = GraphDBConfig(
                    db_type=db_type,
                    neo4j_config=neo4j_config,
                    **{k: v for k, v in config_dict.items() if k not in ["db_type", "neo4j_config"]}
                )
            else:
                raise GraphConfigException(f"Unsupported db_type: {db_type}")

            return cls.create(config)

        except GraphConfigException:
            raise
        except Exception as e:
            raise GraphConfigException(f"Failed to create instance from config dict: {e}")

    @classmethod
    def create_from_env(cls) -> GraphDatabase:
        """
        从环境变量创建实例

        Returns:
            图数据库实例
        """
        config = GraphDBConfig.from_env()
        return cls.create(config)

    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的数据库类型列表"""
        return list(cls._registry.keys())

    @classmethod
    def is_supported(cls, db_type: str) -> bool:
        """检查是否支持指定的数据库类型"""
        return db_type.lower() in cls._registry