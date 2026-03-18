from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import os
from pathlib import Path


@dataclass
class QdrantConfig:
    """Qdrant 数据库配置"""
    host: str = "localhost"
    port: int = 6333
    url: Optional[str] = None  # 如果提供URL，则忽略host和port
    api_key: Optional[str] = None
    prefer_grpc: bool = False
    timeout: Optional[float] = None
    https: Optional[bool] = None
    prefix: Optional[str] = None


@dataclass
class MilvusConfig:
    """Milvus 数据库配置"""
    host: str = "localhost"
    port: int = 19530
    uri: Optional[str] = None  # 如果提供URI，则忽略host和port
    user: Optional[str] = None
    password: Optional[str] = None
    db_name: str = "default"
    token: Optional[str] = None  # 认证token
    secure: bool = False
    client_timeout: Optional[float] = None

    # Milvus 特定配置
    index_params: Dict[str, Any] = field(default_factory=dict)
    search_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorDBConfig:
    """向量数据库通用配置"""
    db_type: str  # 'qdrant' 或 'milvus'

    # 通用配置
    max_connections: int = 10
    connection_timeout: float = 30.0
    operation_timeout: float = 60.0
    retry_attempts: int = 3
    retry_delay: float = 1.0

    # 数据库特定配置
    qdrant_config: Optional[QdrantConfig] = None
    milvus_config: Optional[MilvusConfig] = None

    # 日志配置
    enable_logging: bool = True
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "VectorDBConfig":
        """从环境变量加载配置"""
        # 尝试加载 .env 文件（如果存在）
        cls._load_env_file()

        db_type = os.getenv("VECTOR_DB_TYPE", "qdrant").lower()

        if db_type == "qdrant":
            qdrant_config = QdrantConfig(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6333")),
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY"),
                prefer_grpc=os.getenv("QDRANT_PREFER_GRPC", "false").lower() == "true",
                timeout=float(os.getenv("QDRANT_TIMEOUT", "30.0")) if os.getenv("QDRANT_TIMEOUT") else None,
                https=os.getenv("QDRANT_HTTPS", "false").lower() == "true" if os.getenv("QDRANT_HTTPS") else None,
                prefix=os.getenv("QDRANT_PREFIX"),
            )
            return cls(db_type=db_type, qdrant_config=qdrant_config)

        elif db_type == "milvus":
            milvus_config = MilvusConfig(
                host=os.getenv("MILVUS_HOST", "localhost"),
                port=int(os.getenv("MILVUS_PORT", "19530")),
                uri=os.getenv("MILVUS_URI"),
                user=os.getenv("MILVUS_USER"),
                password=os.getenv("MILVUS_PASSWORD"),
                db_name=os.getenv("MILVUS_DB_NAME", "default"),
                token=os.getenv("MILVUS_TOKEN"),
                secure=os.getenv("MILVUS_SECURE", "false").lower() == "true",
                client_timeout=float(os.getenv("MILVUS_CLIENT_TIMEOUT", "30.0")) if os.getenv("MILVUS_CLIENT_TIMEOUT") else None,
            )
            return cls(db_type=db_type, milvus_config=milvus_config)

        else:
            raise ValueError(f"Unsupported vector database type: {db_type}")

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
        # 支持动态注册的类型，所以只检查基本支持的类型
        supported_base_types = ["qdrant", "milvus"]
        if self.db_type.lower() not in supported_base_types:
            # 不抛出异常，允许自定义类型
            pass

        if self.db_type == "qdrant" and not self.qdrant_config:
            raise ValueError("Qdrant config is required when db_type is 'qdrant'")

        if self.db_type == "milvus" and not self.milvus_config:
            raise ValueError("Milvus config is required when db_type is 'milvus'")