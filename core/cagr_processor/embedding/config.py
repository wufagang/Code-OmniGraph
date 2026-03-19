"""嵌入模型配置类

使用 @dataclass 模式，与 graph_dao/config.py 和 embedding_dao/config.py 保持一致。
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from cagr_common.exceptions import EmbeddingConfigException


def _load_env_file() -> None:
    """按优先级搜索并加载 .env 文件（cwd -> parent -> core/ -> 仓库根）"""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    import pathlib
    start = pathlib.Path(__file__).resolve()
    candidates = [
        pathlib.Path.cwd() / ".env",
        start.parent.parent.parent / ".env",          # core/
        start.parent.parent.parent.parent / ".env",   # 仓库根
    ]
    for path in candidates:
        if path.exists():
            load_dotenv(path, override=False)
            break


# ==================== 各 Provider 具体配置 ====================

@dataclass
class OpenAIEmbeddingConfig:
    """OpenAI 嵌入模型配置"""
    api_key: str = ""
    model: str = "text-embedding-3-small"   # 默认维度 1536
    base_url: Optional[str] = None          # Azure / 代理地址
    timeout: float = 30.0
    max_tokens: int = 8191                  # text-embedding-3-small token 上限


@dataclass
class GeminiEmbeddingConfig:
    """Google Gemini 嵌入模型配置"""
    api_key: str = ""
    model: str = "models/text-embedding-004"  # 默认维度 768
    task_type: str = "RETRIEVAL_DOCUMENT"
    timeout: float = 30.0
    max_tokens: int = 2048


@dataclass
class OllamaEmbeddingConfig:
    """Ollama 本地嵌入模型配置"""
    host: str = "localhost"
    port: int = 11434
    model: str = "nomic-embed-text"         # 默认维度 768
    timeout: float = 60.0
    max_tokens: int = 8192


# ==================== 通用配置门面 ====================

@dataclass
class EmbeddingConfig:
    """嵌入模型通用配置

    通过 provider 字段路由到具体的实现：
        EmbeddingConfig(provider="openai", openai_config=OpenAIEmbeddingConfig(...))

    推荐使用 from_env() 从环境变量加载。
    """
    provider: str                                              # 'openai' / 'gemini' / 'ollama'
    openai_config: Optional[OpenAIEmbeddingConfig] = None
    gemini_config: Optional[GeminiEmbeddingConfig] = None
    ollama_config: Optional[OllamaEmbeddingConfig] = None
    batch_size: int = 100
    enable_logging: bool = True

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """从环境变量构建配置

        关键环境变量：
            EMBEDDING_PROVIDER      openai / gemini / ollama（默认 openai）
            OPENAI_API_KEY
            OPENAI_EMBEDDING_MODEL
            OPENAI_API_BASE         可选，代理/Azure 地址
            GEMINI_API_KEY
            GEMINI_EMBEDDING_MODEL
            OLLAMA_HOST             默认 localhost
            OLLAMA_PORT             默认 11434
            OLLAMA_EMBEDDING_MODEL  默认 nomic-embed-text
            EMBEDDING_BATCH_SIZE    默认 100
        """
        _load_env_file()
        provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))

        openai_cfg = None
        gemini_cfg = None
        ollama_cfg = None

        if provider == "openai":
            openai_cfg = OpenAIEmbeddingConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                base_url=os.getenv("OPENAI_API_BASE") or None,
            )
        elif provider == "gemini":
            gemini_cfg = GeminiEmbeddingConfig(
                api_key=os.getenv("GEMINI_API_KEY", ""),
                model=os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004"),
            )
        elif provider == "ollama":
            port_str = os.getenv("OLLAMA_PORT", "11434")
            ollama_cfg = OllamaEmbeddingConfig(
                host=os.getenv("OLLAMA_HOST", "localhost"),
                port=int(port_str),
                model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
            )
        else:
            raise EmbeddingConfigException(
                f"Unsupported embedding provider: '{provider}'. "
                "Supported: openai, gemini, ollama",
                provider=provider,
            )

        config = cls(
            provider=provider,
            openai_config=openai_cfg,
            gemini_config=gemini_cfg,
            ollama_config=ollama_cfg,
            batch_size=batch_size,
        )
        config.validate()
        return config

    def validate(self) -> None:
        """校验配置完整性"""
        if not self.provider:
            raise EmbeddingConfigException("provider must not be empty")

        if self.provider == "openai":
            if self.openai_config is None:
                raise EmbeddingConfigException(
                    "openai_config is required when provider='openai'", provider="openai"
                )
        elif self.provider == "gemini":
            if self.gemini_config is None:
                raise EmbeddingConfigException(
                    "gemini_config is required when provider='gemini'", provider="gemini"
                )
        elif self.provider == "ollama":
            if self.ollama_config is None:
                raise EmbeddingConfigException(
                    "ollama_config is required when provider='ollama'", provider="ollama"
                )
        else:
            raise EmbeddingConfigException(
                f"Unsupported provider: '{self.provider}'", provider=self.provider
            )

        if self.batch_size <= 0:
            raise EmbeddingConfigException("batch_size must be > 0")
