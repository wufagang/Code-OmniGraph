"""Embedding 接口定义

纯粹的文本 → 向量接口，与向量存储（embedding_dao）和业务服务（embedding_service）完全解耦。
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class EmbeddingModel(ABC):
    """文本嵌入模型接口

    职责：将文本转换为浮点数向量。
    不涉及向量存储、业务逻辑或 LLM 调用。

    使用方式：
        config = EmbeddingConfig.from_env()
        model = EmbeddingFactory.create(config)
        vector = model.embed("public void bar() {}")
        vectors = model.embedBatch(["text1", "text2"])
    """

    @abstractmethod
    def preprocessText(self, text: str) -> str:
        """预处理单条文本

        包含：去首尾空白、压缩多余空行、按模型 token 上限截断。
        各实现可 override 以添加特定清洗逻辑。

        Args:
            text: 原始输入文本

        Returns:
            处理后的文本字符串
        """

    @abstractmethod
    def preprocessTexts(self, texts: List[str]) -> List[str]:
        """批量预处理文本，对列表中每条文本调用 preprocessText

        Args:
            texts: 原始文本列表

        Returns:
            处理后的文本列表，顺序与输入一致
        """

    @abstractmethod
    def detectDimension(self) -> int:
        """从配置/模型元数据中读取已知向量维度

        不调用远程 API，仅查询内置维度映射表或配置值。

        Returns:
            向量维度整数（如 1536、768）
        """

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """将单条文本转换为向量

        实现应在内部调用 preprocessText 进行预处理，再调用模型 API。

        Args:
            text: 输入文本

        Returns:
            浮点数向量列表

        Raises:
            EmbeddingConnectionException: 连接失败（可重试）
            EmbeddingRateLimitException: API 限流
            EmbeddingTimeoutException: 请求超时
        """

    @abstractmethod
    def embedBatch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
    ) -> List[List[float]]:
        """批量文本转向量

        支持分批调用以控制 API 请求压力，各批次结果按输入顺序拼接。

        Args:
            texts: 输入文本列表
            batch_size: 每批次大小，None 时使用配置默认值

        Returns:
            向量列表，顺序与输入文本一致
        """

    @abstractmethod
    def getDimension(self) -> int:
        """返回当前模型的向量维度

        通常返回 detectDimension() 的结果或其缓存值。

        Returns:
            向量维度整数
        """

    @abstractmethod
    def getProvider(self) -> str:
        """返回 provider 标识字符串

        Returns:
            provider 名称，如 'openai' / 'gemini' / 'ollama'
        """
