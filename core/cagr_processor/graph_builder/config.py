"""图数据库配置定义"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class Neo4jConfig:
    """Neo4j 连接配置"""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "password"
    database: Optional[str] = None     # None 表示使用默认数据库
    max_connection_pool_size: int = 50
    connection_timeout: float = 30.0
    max_transaction_retry_time: float = 30.0
    encrypted: bool = False


@dataclass
class GraphDBConfig:
    """图数据库通用配置"""
    db_type: str                       # "neo4j" 或未来扩展的其他类型

    # 批量写入配置
    default_batch_size: int = 500      # UNWIND 批量写入的默认批大小

    # 连接配置（各子类使用自己的具体配置）
    neo4j_config: Optional[Neo4jConfig] = None

    # 日志配置
    enable_logging: bool = True
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "GraphDBConfig":
        """从环境变量加载配置"""
        # 尝试加载 .env 文件（如果存在）
        cls._load_env_file()

        db_type = os.getenv("GRAPH_DB_TYPE", "neo4j").lower()

        if db_type == "neo4j":
            neo4j_config = Neo4jConfig(
                uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                username=os.getenv("NEO4J_USERNAME", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD", "password"),
                database=os.getenv("NEO4J_DATABASE"),
                max_connection_pool_size=int(os.getenv("NEO4J_MAX_POOL_SIZE", "50")),
                connection_timeout=float(os.getenv("NEO4J_CONNECTION_TIMEOUT", "30.0")),
                encrypted=os.getenv("NEO4J_ENCRYPTED", "false").lower() == "true",
            )
            return cls(db_type=db_type, neo4j_config=neo4j_config)

        raise ValueError(f"Unsupported graph database type: {db_type}")

    @staticmethod
    def _load_env_file():
        """加载 .env 文件"""
        # 尝试在当前目录和父目录查找 .env 文件
        current_dir = Path.cwd()
        possible_paths = [
            current_dir / ".env",
            current_dir.parent / ".env",
            current_dir / "core" / ".env",
            Path(__file__).parent.parent.parent / ".env",
        ]

        # 查找第一个存在的 .env 文件
        env_file = None
        for path in possible_paths:
            if path.exists():
                env_file = path
                break

        if env_file:
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                # 如果没有安装 python-dotenv，则跳过
                pass

    def validate(self) -> None:
        """验证配置有效性"""
        if not self.db_type:
            raise ValueError("db_type must be specified")

        if self.db_type == "neo4j" and not self.neo4j_config:
            raise ValueError("neo4j_config is required when db_type is 'neo4j'")

        if self.default_batch_size <= 0:
            raise ValueError("default_batch_size must be positive")
