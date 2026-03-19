"""Google Gemini 嵌入模型实现"""

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
    import google.generativeai as _genai
    GEMINI_AVAILABLE = True
except ImportError:
    _genai = None  # type: ignore
    GEMINI_AVAILABLE = False

# 已知模型维度映射
_DIMENSION_MAP: dict = {
    "models/text-embedding-004": 768,
    "models/embedding-001": 768,
}


class GeminiEmbedding(BaseEmbeddingModel):
    """Google Gemini 文本嵌入实现

    支持 models/text-embedding-004 和 models/embedding-001。
    通过 task_type 控制嵌入用途（RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY / SEMANTIC_SIMILARITY）。
    """

    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        if not GEMINI_AVAILABLE:
            raise EmbeddingConfigException(
                "google-generativeai package is not installed. "
                "Run: pip install google-generativeai",
                provider="gemini",
            )
        cfg = config.gemini_config
        if cfg is None:
            raise EmbeddingConfigException(
                "gemini_config is required for GeminiEmbedding", provider="gemini"
            )
        _genai.configure(api_key=cfg.api_key)
        self._model = cfg.model
        self._task_type = cfg.task_type
        self._dimension: Optional[int] = None

    @retry_on_failure(max_attempts=3, delay=1.0)
    def embed(self, text: str) -> List[float]:
        """将单条文本转换为向量"""
        processed = self.preprocessText(text)
        try:
            result = _genai.embed_content(
                model=self._model,
                content=processed,
                task_type=self._task_type,
            )
            return result["embedding"]
        except Exception as e:
            msg = str(e).lower()
            if "quota" in msg or "rate" in msg:
                raise EmbeddingRateLimitException(str(e), provider="gemini") from e
            if "timeout" in msg or "deadline" in msg:
                raise EmbeddingTimeoutException(str(e), provider="gemini") from e
            if "connect" in msg or "network" in msg or "unavailable" in msg:
                raise EmbeddingConnectionException(str(e), provider="gemini") from e
            raise EmbeddingConnectionException(
                f"Gemini embedding failed: {e}", provider="gemini"
            ) from e

    def detectDimension(self) -> int:
        """从内置映射表中读取当前模型的向量维度"""
        return _DIMENSION_MAP.get(self._model, 768)

    def getDimension(self) -> int:
        """返回向量维度（优先使用缓存值）"""
        if self._dimension is None:
            self._dimension = self.detectDimension()
        return self._dimension

    def getProvider(self) -> str:
        return "gemini"
