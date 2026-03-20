#!/usr/bin/env python3
"""
embedding 模块使用示例
=====================
演示从「文本」到「向量」的完整流程，不涉及向量库存储。

运行方式（在仓库根目录）：
    python core/example/cagr_processor/embedding_dao/example_embedding.py

前置条件：
    - Demo 1/2/3：core/.env 中配置 OPENAI_API_KEY
    - Demo 4：本地运行 Ollama，并已拉取 nomic-embed-text 模型
        ollama pull nomic-embed-text
        ollama serve
    - Demo 5：无需任何外部依赖
"""

import os
import sys

# 将仓库根目录加入模块搜索路径，确保可从任意工作目录直接运行
current_file = os.path.abspath(__file__)
core_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

from cagr_processor.embedding import (
    EmbeddingFactory,
    EmbeddingConfig,
    OpenAIEmbeddingConfig,
    OllamaEmbeddingConfig,
    EmbeddingModel,
)
from cagr_processor.embedding.base import BaseEmbeddingModel
from cagr_common.exceptions import (
    EmbeddingConnectionException,
    EmbeddingConfigException,
)

# ---------------------------------------------------------------------------
# 演示用 Java 方法源码片段（真实业务代码场景）
# ---------------------------------------------------------------------------

SAMPLE_METHOD_ORDER = """\
public Order processOrder(OrderRequest request) {
    validateRequest(request);
    Order order = orderRepository.save(Order.from(request));
    paymentService.charge(order);
    notificationService.sendConfirmation(order.getCustomerEmail(), order);
    return order;
}"""

SAMPLE_METHOD_EMAIL = """\
public void sendEmail(String to, String subject, String body) {
    MimeMessage message = mailSender.createMimeMessage();
    MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
    helper.setTo(to);
    helper.setSubject(subject);
    helper.setText(body, true);
    mailSender.send(message);
}"""

SAMPLE_METHOD_USERS = """\
public List<User> findActiveUsers(LocalDate since) {
    return userRepository.findAll().stream()
        .filter(u -> u.isActive() && u.getCreatedAt().isAfter(since))
        .sorted(Comparator.comparing(User::getCreatedAt).reversed())
        .collect(Collectors.toList());
}"""

SAMPLE_METHODS = [SAMPLE_METHOD_ORDER, SAMPLE_METHOD_EMAIL, SAMPLE_METHOD_USERS]


# ---------------------------------------------------------------------------
# Demo 1：使用 OpenAI 创建模型并执行单次 embed
# ---------------------------------------------------------------------------

def demo1_openai_single() -> EmbeddingModel:
    """
    演示要点：
    1. 显式构建 EmbeddingConfig（provider="openai"），不依赖环境变量
    2. 通过 EmbeddingFactory.create() 获取 EmbeddingModel 实例
    3. 调用 model.embed() 将单段文本转换为浮点向量
    4. 打印 provider、维度、向量前 8 个值
    """
    print("\n" + "=" * 60)
    print("Demo 1：OpenAI 单次 embed")
    print("=" * 60)

    config = EmbeddingFactory.create_from_env()
    # 2. 创建模型实例
    model = EmbeddingFactory.create(config)

    print(f"  provider    : {model.getProvider()}")
    print(f"  模型维度    : {model.detectDimension()}  (detectDimension，本地读取配置，无 API 调用)")

    # 3. 单次 embed
    text = SAMPLE_METHOD_ORDER
    print(f"\n  待向量化文本（前 80 字符）：\n  {text[:80].strip()} ...")
    vector = model.embed(text)

    print(f"\n  向量维度     : {len(vector)}")
    print(f"  前 8 个值    : {[round(v, 6) for v in vector[:8]]}")

    return model


# ---------------------------------------------------------------------------
# Demo 2：批量 embed（embedBatch）
# ---------------------------------------------------------------------------

def demo2_batch_embed(model: EmbeddingModel) -> None:
    """
    演示要点：
    1. 将多段文本一次性传给 embedBatch()
    2. 打印每条文本对应的向量维度和前 3 个值
    3. 说明 embedBatch 与多次调用 embed 的关系（底层分批调用 embed）
    """
    print("\n" + "=" * 60)
    print("Demo 2：批量 embed（embedBatch）")
    print("=" * 60)

    if model is None:
        print("[跳过] Demo 1 未能创建模型（OPENAI_API_KEY 未设置）。")
        return

    texts = SAMPLE_METHODS
    print(f"  待向量化文本数量: {len(texts)}")

    # embedBatch 内部按 batch_size 分批，每批调用一次 embed
    vectors = model.embedBatch(texts)

    for i, (text, vec) in enumerate(zip(texts, vectors)):
        method_name = text.split("(")[0].strip().split()[-1]
        print(f"\n  [{i + 1}] {method_name}()")
        print(f"      向量维度  : {len(vec)}")
        print(f"      前 3 个值 : {[round(v, 6) for v in vec[:3]]}")

    print(f"\n  共产生 {len(vectors)} 个向量，形状 {len(vectors)} × {len(vectors[0])}")


# ---------------------------------------------------------------------------
# Demo 3：从环境变量创建模型（create_from_env）
# ---------------------------------------------------------------------------

def demo3_from_env() -> None:
    """
    演示要点：
    1. 不写任何硬编码配置，完全由环境变量驱动
    2. EmbeddingFactory.create_from_env() 自动读取 EMBEDDING_PROVIDER 及对应的 key/host
    3. 适合生产环境或 Docker 容器化部署场景
    """
    print("\n" + "=" * 60)
    print("Demo 3：从环境变量创建模型（create_from_env）")
    print("=" * 60)

    # 显示当前生效的 provider 配置
    provider = os.getenv("EMBEDDING_PROVIDER", "openai")
    print(f"  EMBEDDING_PROVIDER = {provider}")

    try:
        model = EmbeddingFactory.create_from_env()
        print(f"  成功创建模型 → provider: {model.getProvider()}, 维度: {model.detectDimension()}")

        query = "查找所有活跃用户的业务逻辑"
        vector = model.embed(query)
        print(f"\n  查询文本  : {query}")
        print(f"  向量维度  : {len(vector)}")
        print(f"  前 5 个值 : {[round(v, 6) for v in vector[:5]]}")

    except EmbeddingConfigException as e:
        print(f"[跳过] 配置错误：{e}")
    except Exception as e:
        print(f"[跳过] 创建失败：{e}")


# ---------------------------------------------------------------------------
# Demo 4：使用 Ollama 本地模型（无需 API Key）
# ---------------------------------------------------------------------------

def demo4_ollama() -> None:
    """
    演示要点：
    1. Ollama 在本地运行，无需任何 API key
    2. nomic-embed-text 输出 768 维向量（vs OpenAI 的 1536 维）
    3. 展示切换 provider 只需更换 config，业务代码无需改动
    4. 若 Ollama 未启动，打印友好提示而非直接抛出异常
    """
    print("\n" + "=" * 60)
    print("Demo 4：Ollama 本地模型（无需 API Key）")
    print("=" * 60)

    config = EmbeddingConfig(
        provider="ollama",
        ollama_config=OllamaEmbeddingConfig(
            host="localhost",
            port=11434,
            model="nomic-embed-text",   # 输出维度 768
        ),
    )

    try:
        model = EmbeddingFactory.create(config)
        print(f"  provider    : {model.getProvider()}")
        print(f"  模型维度    : {model.detectDimension()}  (nomic-embed-text)")

        text = SAMPLE_METHOD_USERS
        print(f"\n  待向量化文本（前 80 字符）：\n  {text[:80].strip()} ...")
        vector = model.embed(text)

        print(f"\n  向量维度     : {len(vector)}")
        print(f"  前 8 个值    : {[round(v, 6) for v in vector[:8]]}")

    except EmbeddingConnectionException as e:
        print(f"[跳过] 无法连接 Ollama（localhost:11434）：{e}")
        print("  请确认 Ollama 已启动：ollama serve")
        print("  并已拉取模型：ollama pull nomic-embed-text")
    except EmbeddingConfigException as e:
        print(f"[跳过] 配置错误：{e}")
    except Exception as e:
        print(f"[跳过] 创建失败（{type(e).__name__}）：{e}")


# ---------------------------------------------------------------------------
# Demo 5：注册并使用自定义 Provider（无需任何网络调用）
# ---------------------------------------------------------------------------

class HashEmbedding(BaseEmbeddingModel):
    """
    自定义嵌入模型示例：基于字符哈希生成固定维度向量。
    仅用于演示如何扩展 EmbeddingFactory，不适用于生产。
    """

    DIM = 256

    def embed(self, text: str) -> list:
        """将文本哈希值映射到 [-1, 1] 范围内的 256 维向量"""
        processed = self.preprocessText(text)
        seed = hash(processed)
        # 用确定性伪随机数填充向量（不依赖任何外部服务）
        import random
        rng = random.Random(seed)
        return [rng.uniform(-1.0, 1.0) for _ in range(self.DIM)]

    def detectDimension(self) -> int:
        return self.DIM

    def getDimension(self) -> int:
        return self.DIM

    def getProvider(self) -> str:
        return "hash"


def demo5_custom_provider() -> None:
    """
    演示要点：
    1. 继承 BaseEmbeddingModel，实现 4 个必要方法
    2. 通过 EmbeddingFactory.register() 注册新 provider
    3. 之后可用标准 EmbeddingFactory.create() 创建，调用方无需关心实现细节
    4. 整个过程无网络调用，适合本地调试和离线测试
    """
    print("\n" + "=" * 60)
    print("Demo 5：注册自定义 Provider（无网络调用）")
    print("=" * 60)

    # 1. 注册自定义实现
    EmbeddingFactory.register("hash", HashEmbedding)
    print(f"  已注册 provider: {EmbeddingFactory.get_supported_providers()}")

    # 2. 构建配置（provider 字段匹配注册名即可）
    #    EmbeddingConfig.validate() 只检查 provider 字段和对应 config 是否存在，
    #    "hash" 是自定义 provider，直接绕过 validate，使用低层 API
    config = EmbeddingConfig.__new__(EmbeddingConfig)
    config.provider = "hash"
    config.openai_config = None
    config.gemini_config = None
    config.ollama_config = None
    config.batch_size = 100
    config.enable_logging = False

    # 3. 创建模型并 embed
    model = EmbeddingFactory.create(config)
    print(f"  provider    : {model.getProvider()}")
    print(f"  模型维度    : {model.getDimension()}")

    text = SAMPLE_METHOD_EMAIL
    vector = model.embed(text)
    print(f"\n  待向量化文本（前 80 字符）：\n  {text[:80].strip()} ...")
    print(f"\n  向量维度     : {len(vector)}")
    print(f"  前 8 个值    : {[round(v, 6) for v in vector[:8]]}")

    # 4. 验证确定性：相同输入两次 embed 应得到完全相同的向量
    vector2 = model.embed(text)
    assert vector == vector2, "自定义模型应保证相同输入输出相同向量"
    print("\n  [验证通过] 相同输入两次 embed 结果完全一致（确定性）")

    # 5. 演示 embedBatch
    vectors = model.embedBatch(SAMPLE_METHODS)
    print(f"\n  批量 embed {len(SAMPLE_METHODS)} 条文本 → {len(vectors)} × {len(vectors[0])} 向量矩阵")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Code-OmniGraph embedding 模块演示")
    print("使用说明：")
    print("  Demo 1/2/3 需要 OPENAI_API_KEY（配置在 core/.env）")
    print("  Demo 4     需要本地运行 Ollama 并拉取 nomic-embed-text 模型")
    print("  Demo 5     无需任何外部依赖，始终可运行")

    openai_model = demo1_openai_single()
    demo2_batch_embed(openai_model)
    demo3_from_env()
    demo4_ollama()
    demo5_custom_provider()

    print("\n" + "=" * 60)
    print("所有 Demo 执行完毕")
    print("=" * 60)
