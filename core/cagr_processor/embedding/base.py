"""BaseEmbeddingModel：提供通用预处理、批处理和重试逻辑的抽象基类"""

import logging
import re
import time
from abc import abstractmethod
from typing import List, Optional

from cagr_common.exceptions import EmbeddingConnectionException
from cagr_processor.embedding.interfaces import EmbeddingModel


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器：仅对 EmbeddingConnectionException 重试，其他异常直接抛出"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(self, *args, **kwargs)
                except EmbeddingConnectionException as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


class BaseEmbeddingModel(EmbeddingModel):
    """嵌入模型基础抽象类

    提供：
    - preprocessText / preprocessTexts 的通用实现（截断 + 清洗）
    - embedBatch 的分批实现（调用 embed）
    - 日志和配置基础设施

    子类必须实现：embed、detectDimension、getDimension、getProvider
    子类可 override：preprocessText（添加特定清洗逻辑）
    """

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # preprocessText / preprocessTexts（通用实现，子类可 override）
    # ------------------------------------------------------------------

    def preprocessText(self, text: str) -> str:
        """通用文本预处理：去空白、压缩空行、按字符数截断"""
        if not text:
            return ""

        # 1. 去首尾空白
        text = text.strip()

        # 2. 压缩连续空行（3行以上空行 → 2行）
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 3. 去除行尾空白
        text = '\n'.join(line.rstrip() for line in text.splitlines())

        # 4. 按 max_tokens（近似字符数）截断
        max_tokens = self._get_max_tokens()
        if max_tokens and len(text) > max_tokens:
            text = text[:max_tokens]

        return text

    def preprocessTexts(self, texts: List[str]) -> List[str]:
        """批量预处理：逐条调用 preprocessText"""
        return [self.preprocessText(t) for t in texts]

    # ------------------------------------------------------------------
    # embedBatch（基类提供分批调用实现）
    # ------------------------------------------------------------------

    def embedBatch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
    ) -> List[List[float]]:
        """分批将文本列表转换为向量列表"""
        if not texts:
            return []

        effective_batch_size = batch_size or getattr(self.config, 'batch_size', 100)
        results: List[List[float]] = []

        for i in range(0, len(texts), effective_batch_size):
            batch = texts[i: i + effective_batch_size]
            for text in batch:
                results.append(self.embed(text))

        return results

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _get_max_tokens(self) -> Optional[int]:
        """从具体配置对象中取 max_tokens 字段，找不到时返回 None"""
        provider = self.getProvider()
        config_field = f"{provider}_config"
        specific_config = getattr(self.config, config_field, None)
        if specific_config is not None:
            return getattr(specific_config, 'max_tokens', None)
        return None

    def _log(self, msg: str, level: str = "debug") -> None:
        if getattr(self.config, 'enable_logging', True):
            getattr(self.logger, level)(msg)
