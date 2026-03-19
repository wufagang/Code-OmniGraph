"""Ollama 本地嵌入模型实现"""

import json
import urllib.error
import urllib.request
from typing import List, Optional

from cagr_common.exceptions import (
    EmbeddingConnectionException,
    EmbeddingConfigException,
    EmbeddingTimeoutException,
)
from cagr_processor.embedding.base import BaseEmbeddingModel, retry_on_failure
from cagr_processor.embedding.config import EmbeddingConfig

try:
    import ollama as _ollama
    OLLAMA_SDK_AVAILABLE = True
except ImportError:
    _ollama = None  # type: ignore
    OLLAMA_SDK_AVAILABLE = False

# 已知模型维度映射
_DIMENSION_MAP: dict = {
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024,
    "all-minilm": 384,
    "bge-m3": 1024,
}


class OllamaEmbedding(BaseEmbeddingModel):
    """Ollama 本地嵌入模型实现

    优先使用 ollama Python SDK；若未安装则降级为直接调用 HTTP REST API。
    默认模型 nomic-embed-text，需在本地 Ollama 服务中预先 pull。
    """

    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        cfg = config.ollama_config
        if cfg is None:
            raise EmbeddingConfigException(
                "ollama_config is required for OllamaEmbedding", provider="ollama"
            )
        self._host = cfg.host
        self._port = cfg.port
        self._model = cfg.model
        self._timeout = cfg.timeout
        self._base_url = f"http://{self._host}:{self._port}"
        self._dimension: Optional[int] = None

    @retry_on_failure(max_attempts=3, delay=1.0)
    def embed(self, text: str) -> List[float]:
        """将单条文本转换为向量"""
        processed = self.preprocessText(text)
        if OLLAMA_SDK_AVAILABLE:
            return self._embed_via_sdk(processed)
        return self._embed_via_http(processed)

    def _embed_via_sdk(self, text: str) -> List[float]:
        try:
            client = _ollama.Client(host=self._base_url)
            response = client.embeddings(model=self._model, prompt=text)
            return response["embedding"]
        except Exception as e:
            raise EmbeddingConnectionException(
                f"Ollama SDK embedding failed: {e}", provider="ollama"
            ) from e

    def _embed_via_http(self, text: str) -> List[float]:
        """通过 HTTP REST 调用 Ollama /api/embeddings"""
        url = f"{self._base_url}/api/embeddings"
        payload = json.dumps({"model": self._model, "prompt": text}).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode())
                return data["embedding"]
        except urllib.error.URLError as e:
            reason = str(e.reason) if hasattr(e, 'reason') else str(e)
            if "timed out" in reason.lower():
                raise EmbeddingTimeoutException(
                    f"Ollama request timed out: {e}", provider="ollama"
                ) from e
            raise EmbeddingConnectionException(
                f"Ollama HTTP request failed: {e}", provider="ollama"
            ) from e
        except Exception as e:
            raise EmbeddingConnectionException(
                f"Ollama embedding failed: {e}", provider="ollama"
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
        return "ollama"
