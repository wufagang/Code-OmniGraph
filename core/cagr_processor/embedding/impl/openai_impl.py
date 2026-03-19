"""OpenAI 嵌入模型实现"""

from typing import List, Optional

from cagr_common.exceptions import (
    EmbeddingConnectionException,
    EmbeddingConfigException,
    EmbeddingRateLimitException,
    EmbeddingTimeoutException,
)
from cagr_processor.embedding.base import BaseEmbeddingModel, retry_on_failure
from cagr_processor.embedding.config import EmbeddingConfig

try:
    import openai as _openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 已知模型维度映射（model_name -> dimension）
_DIMENSION_MAP: dict = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


class OpenAIEmbedding(BaseEmbeddingModel):
    """OpenAI 文本嵌入实现

    支持 text-embedding-3-small / text-embedding-3-large / text-embedding-ada-002。
    通过 OpenAIEmbeddingConfig.base_url 支持 Azure OpenAI 和代理地址。
    """

    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise EmbeddingConfigException(
                "openai package is not installed. Run: pip install openai",
                provider="openai",
            )
        cfg = config.openai_config
        if cfg is None:
            raise EmbeddingConfigException(
                "openai_config is required for OpenAIEmbedding", provider="openai"
            )
        kwargs = {"api_key": cfg.api_key, "timeout": cfg.timeout}
        if cfg.base_url:
            kwargs["base_url"] = cfg.base_url
        self._client = _openai.OpenAI(**kwargs)
        self._model = cfg.model
        self._dimension: Optional[int] = None

    @retry_on_failure(max_attempts=3, delay=1.0)
    def embed(self, text: str) -> List[float]:
        """将单条文本转换为向量"""
        processed = self.preprocessText(text)
        try:
            response = self._client.embeddings.create(
                model=self._model,
                input=processed,
            )
            return response.data[0].embedding
        except _openai.RateLimitError as e:
            raise EmbeddingRateLimitException(str(e), provider="openai") from e
        except _openai.APITimeoutError as e:
            raise EmbeddingTimeoutException(str(e), provider="openai") from e
        except _openai.APIConnectionError as e:
            raise EmbeddingConnectionException(str(e), provider="openai") from e
        except Exception as e:
            raise EmbeddingConnectionException(
                f"OpenAI embedding failed: {e}", provider="openai"
            ) from e

    def detectDimension(self) -> int:
        """从内置映射表中读取当前模型的向量维度"""
        return _DIMENSION_MAP.get(self._model, 1536)

    def getDimension(self) -> int:
        """返回向量维度（优先使用缓存值）"""
        if self._dimension is None:
            self._dimension = self.detectDimension()
        return self._dimension

    def getProvider(self) -> str:
        return "openai"
