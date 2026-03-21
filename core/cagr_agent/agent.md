# Project Genesis：自我演进式软件生命周期引擎（修订版 v2）

> **修订说明**：本版本针对 v1 的六个核心落地问题进行了系统性修订。
> 原版的核心哲学和三权分立架构保持不变，新增了确定性质量门禁、有界追问、
> 分层 Auditor、Traceback 策略引擎等机制，使方案从"概念架构"升级为"可执行工程规范"。

---

## 一、哪些设计保持不变

以下是 v1 中正确的核心判断，本版本完整保留：

1. **三权分立的权力结构**：Skeptic（立法/需求）、Oracle（立法/架构）、Adversary+Coder（执行）、Auditor（司法），解决了 AI 串通妥协问题
2. **信息不对称（Visibility Masking）**：每个 Agent 只看自己该看的东西，防止幻觉传染
3. **物理隔离通信协议**：Adversary 和 Coder 之间只通过代码文件和报错日志通信，绝对不共享 Context
4. **契约优先（Contract-First）**：Oracle 先输出 JSON Schema / OpenAPI / 状态机，下游基于契约工作
5. **单向阀（Check-Valve）拓扑**：每个阶段之间必须经过 Auditor 裁决，无法跨越
6. **Coder 自愈式编码循环**：Traceback → 修复 → 重跑的闭环逻辑正确

---

## 二、v1 的六个问题与对应修订

### 问题 1：Adversary 质量无确定性保证

**原问题**：Auditor 用 LLM 判断测试是否"足够恶意"，缺少确定性锚点。

**修订方案**：引入 `QualityGateEvaluator`（纯 Python，不含 LLM），执行以下硬性数值检测：

| 指标 | 工具 | 阈值（环境变量可配） |
|---|---|---|
| 分支覆盖率（Branch Coverage） | `pytest-cov` | `QUALITY_GATE_BRANCH_COVERAGE`，默认 85% |
| 变异测试分数（Mutation Score） | `mutmut` | `QUALITY_GATE_MUTATION_SCORE`，默认 70% |
| 每字段边界类型数 | 统计 TestManifest | `QUALITY_GATE_BOUNDARY_PER_FIELD`，默认 3 种 |
| 并发场景数量 | 统计 TestManifest | `QUALITY_GATE_CONCURRENT_SCENARIOS`，默认 1 个 |

Adversary 除提交测试脚本外，**还必须提交 TestManifest JSON**，声明覆盖了哪些端点、哪些字段做了哪些边界测试。Auditor 的阀门 3 不再是 LLM 主观判断，而是调用 `QualityGateEvaluator` 获取 `QualityGateReport`，拒绝原因形如：`REJECTED: branch_coverage=72% < threshold=85%`。

---

### 问题 2：Memory Traceback 触发条件未定义

**原问题**：回滚的触发条件、范围边界、用户确认节点都未定义，有无限循环风险。

**修订方案**：引入 `TracebackPolicy`（纯 Python 状态机，不含 LLM）和 `ErrorClassifier`（基于规则的分类器）。

**触发条件**（必须同时满足才触发 Traceback，否则继续自愈）：
- 条件 A：Coder 自愈轮次 `>= CODER_MAX_SELF_HEAL_TURNS`（默认 5，环境变量可配）
- 条件 B：`ErrorClassifier` 识别失败根因为 `CONTRACT_MISMATCH` 或 `ARCHITECTURE_DEFECT`，而非 `IMPLEMENTATION_ERROR`

**ErrorClassifier 分类规则**（基于异常类型，确定性）：
- `CONTRACT_MISMATCH`：`AttributeError / KeyError / TypeError / schema 字段不存在` → 需回滚 Oracle
- `ARCHITECTURE_DEFECT`：`IntegrityError / ConstraintViolation / ForeignKeyConstraint` → 需回滚 Oracle 甚至 Skeptic
- `IMPLEMENTATION_ERROR`：其他所有错误 → 继续 Coder 自愈循环

**回滚层级与硬性计数上限**：

```
Layer 1（自动触发）：回滚到 Oracle，从 Checkpoint 恢复 PRD
  → layer1_rollback_count 上限：3 次，超出自动升级到 Layer 2

Layer 2（Layer 1 失败 3 次后触发）：回滚到 Skeptic，重新收敛需求
  → layer2_rollback_count 上限：2 次，超出自动升级到 Layer 3

Layer 3（不自动触发）：暂停 Pipeline，强制用户确认
  → 向用户展示：根因分析 + 当前 Traceback 层级 + 三个选项（继续/接受/终止）
  → 超时（默认 1 小时）则 Pipeline 进入 SUSPENDED 状态
```

---

### 问题 3：TLA+ 落地障碍

**原问题**：TLA+ spec 若由 LLM 生成则语义必然有误，"已通过验证"成为假保证。

**修订方案**：降格为 `ArchitectureVerifier`（基于 `networkx` 图遍历，确定性算法），Oracle 输出的状态机必须是**标准化 JSON**（不再是任意 Mermaid 文本），作为图算法的直接输入。

**三类确定性检测**：

1. **死锁检测**：DFS 遍历状态机有向图，寻找自锁节点、互相等待的循环依赖、有入边无出边且非终态的状态陷阱
2. **孤立节点检测**：寻找没有入边的非初始态节点（永远无法到达）、没有路径到达任何终态的节点
3. **契约覆盖检测**：对比 OpenAPI 端点列表和状态机中的 transition trigger，每个端点必须有对应的状态转换，否则标记 `UNCOVERED_CONTRACT`

Oracle 的 `state_machine_json` 输出格式要求：

```json
{
  "states": [
    {"id": "s1", "name": "...", "is_initial": true, "is_terminal": false}
  ],
  "transitions": [
    {"from": "s1", "to": "s2", "trigger": "POST /api/login", "condition": "..."}
  ]
}
```

---

### 问题 4：Auditor 全局记忆是 Context Window 瓶颈

**原问题**：单一"全知 Auditor"需同时持有所有阶段产物，超出 Context Window。

**修订方案**：两个并行改造：

**① 将单一 Auditor 拆分为三个专职 AuditorGate**，每个 Gate 的 Context 极小且独立：

| Gate | 位置 | 输入 | 职责 |
|---|---|---|---|
| AuditorGate1（需求审计员） | Skeptic → Oracle | 用户需求 3-5 句摘要 + PRD JSON | 验证 PRD 覆盖原始需求，无过度扩展 |
| AuditorGate2（架构审计员） | Oracle → Adversary | PRD 功能点列表 + 架构端点列表 + VerificationReport | 验证架构端点覆盖所有功能点，且无架构缺陷 |
| AuditorGate3（交付审计员） | Coder → Deploy | `integrity_check_result`(bool) + QualityGateReport + SmellReport | 验证代码未篡改契约，指标达标，无严重气味 |

**② 引入 CheckpointStore（外部状态机）**，承接 Auditor 原来的"全局记忆"职责：

```
CheckpointStore 的核心操作（纯 Python，无 LLM）：
  save(stage, artifact)         → 计算 SHA-256，持久化存储，返回 CheckpointRecord
  get_summary(stage)            → 返回压缩摘要（给下游 AuditorGate 的最小化输入）
  verify_integrity(stage, current) → SHA-256 比对，返回 True/False（替代 Auditor 的哈希计算）
  restore(stage)                → Traceback 回滚时恢复完整 artifact
  save_pipeline_state(state)    → 保存 Pipeline 全局状态（当前阶段、回滚计数、status）
```

哈希计算和比对从 LLM 移到 `CheckpointStore`，AuditorGate3 只接收 `integrity_ok: True/False` 的结论。

---

### 问题 5：Skeptic 交互疲劳风险

**原问题**：无最大追问轮次约束，"循环直到熵减"没有终止保证。

**修订方案**：引入 `SkepticSessionTracker` 和 `SkepticEntropyCalculator`（均为纯 Python，不含 LLM）。

**硬性轮次约束**：`SKEPTIC_MAX_ROUNDS`（默认 5，环境变量可配），每轮最多 3 个问题（强制执行，不只是 Prompt 建议）。

**`SkepticEntropyCalculator` 的计算规则**（确定性，基于 PRD JSON 字段统计）：

```
entropy_score（0.0 = 完全清晰，1.0 = 完全模糊）：
  PRD 中每个值为 None/unknown 的字段        +0.1
  每个未解决的矛盾（矛盾探测发现）           +0.2
  5W1H 中每个未覆盖的维度                   +0.1
```

**`STATUS: READY` 触发条件修改**（满足任一即触发）：
- `entropy_score < 0.2`（数值判断，不是 LLM 的"感觉"）
- `current_round >= max_rounds`（轮次上限硬约束）

**Best-Effort Assumption 机制**（当 `round >= max_rounds` 且 `entropy_score > 0.2` 时）：
- 停止继续追问，为所有未解决字段按行业最佳实践填写默认假设
- 将所有假设追加到 PRD JSON 的 `assumptions: List[str]` 字段，保持透明度和可追溯性
- 向用户展示假设列表，告知"如不符合预期，请在需求确认阶段指出"

---

### 问题 6：Coder 过拟合测试风险

**原问题**：KPI 仅为"通过测试"，可能产生硬编码式"作弊"实现（overfitting to tests）。

**修订方案**：在 Coder 完成后、AuditorGate3 终审前，插入 `CodeReviewAgent`（静态反作弊分析层，基于 Python `ast` 模块，不含 LLM）。

**`SmellDetector` 检测四类代码气味**：

| 气味类型 | 检测方法 | 处理方式 |
|---|---|---|
| `HARDCODED_RESPONSE_SMELL` | AST 检测 `if literal → return literal` 模式 | 触发 Coder 重新生成 + 注入随机化补充测试 |
| `TEST_LITERAL_LEAK_SMELL` | 业务代码与测试脚本字面量集合求交集，重合度过高 | 触发 Adversary 补充新测试，Coder 再次通过 |
| `HOLLOW_IMPLEMENTATION_SMELL` | AST 检测只含 `pass`/`return None`/`raise NotImplementedError` 的方法 | AuditorGate3 直接拒绝放行 |
| `LOW_COMPLEXITY_WARNING` | 核心业务方法圈复杂度 `<= 1` | 记录到审计报告，不自动拒绝 |

**Fuzz Supplement（随机测试注入）**：在 Coder 通过 Adversary 的测试后，自动注入一批由系统基于契约类型定义随机生成的、Coder 无法预见的测试用例。真实逻辑会通过，硬编码作弊会失败。

---

## 三、修订后的五大 Agent 定义

---

### 1. 需求分析师 (The Skeptic) —— 有界熵减机器

**定位**：永远不满足的质疑者，但**在有限轮次内**把发散语言收敛为结构化数据。
**KPI**：`entropy_score < 0.2` 或在 `SKEPTIC_MAX_ROUNDS` 轮次内完成收敛，输出含 `assumptions` 的 PRD JSON。

**输入**：用户的自然语言需求
**输出**：`PRDJson`（含 `features`, `five_w_one_h`, `assumptions`, `entropy_score`, `rounds_used`）

**核心机制（修订后）**：

- **缺失变量扫描**：自动检查 5W1H，对未填充字段增加 `entropy_score`
- **矛盾探测**：发现矛盾时指出，同时对每个矛盾增加 `entropy_score`
- **轮次硬约束**：`SkepticSessionTracker` 维护轮次计数，达到 `max_rounds` 时强制触发 Best-Effort Assumption，不再追问
- **Best-Effort Assumption**：为所有剩余模糊字段填写行业最优假设，追加到 `PRDJson.assumptions`

**System Prompt 骨架（修订）**：

> "你是极其严苛的资深系统分析师 (The Skeptic)。你的任务不是写代码，而是**证伪和暴露盲区**。
>
> 当接收到用户需求时，假设它存在漏洞。检查：1. 边界条件是否缺失？2. 异常流是否未定义？3. 性能预期是否模糊？
>
> 每轮**只输出最致命的 1-3 个问题**，不要输出长篇大论。
>
> 当系统通知你 `MAX_ROUNDS_REACHED`，立即停止追问，为所有 `unknown` 字段按行业最佳实践填写假设，在 `PRDJson.assumptions` 中列出每一条假设，并输出 `STATUS: READY`。
>
> 当 `entropy_score < 0.2` 时，直接输出 `STATUS: READY`，不再追问。"

---

### 2. 架构师 (The Oracle) —— 可验证规则的具象化

**定位**：翻译官与系统建模者，只定义"数据结构"、"接口契约"和"状态流转"。
**KPI**：产出 100% 可被图遍历算法检验的 `ArchContractJson`，通过 `ArchitectureVerifier` 零缺陷验证。

**输入**：CheckpointStore 中的 PRD JSON 摘要（不是用户原始聊天记录）
**输出**：`ArchContractJson`（含 `openapi_spec`, `db_schema`, `state_machine_json`）

**核心机制（修订后）**：

- **DDD**：强制提取聚合根（Aggregate Root）和值对象（Value Object）
- **契约优先**：先定义输入输出格式和类型约束，形成 JSON Schema
- **`state_machine_json` 强制标准化**：必须输出可被程序解析的 JSON 格式（见上方 Schema），禁止仅输出 Mermaid 文本

**System Prompt 骨架（修订）**：

> "你是系统架构师 (The Oracle)。你的大脑只由状态机、数据模式和 API 契约组成。
>
> 将输入的业务需求转化为'形式化规范'，输出：1. 核心实体的严格数据模型。2. 组件间的接口契约（OpenAPI 格式）。3. 系统核心流程的状态转换（必须以如下 JSON Schema 输出，不得仅输出 Mermaid 文本）：
>
> `{ "states": [{"id": "...", "name": "...", "is_initial": bool, "is_terminal": bool}], "transitions": [{"from": "...", "to": "...", "trigger": "HTTP Method + Path", "condition": "..."}] }`
>
> 警告：不要包含任何具体实现代码，你的输出必须是语言无关的拓扑结构。"

---

### 3. 红队测试官 (The Adversary) —— 带清单的破坏者

**定位**：在代码写出之前就开始工作，代表系统会遭遇的所有恶意和意外。
**KPI**：测试套件通过 `QualityGateEvaluator` 的所有数值指标，并提交完整的 `TestManifest`。

**输入**：CheckpointStore 中的架构契约摘要（只看契约，不看代码，保持黑盒测试）
**输出**：测试脚本文件 + `TestManifest JSON`

**核心机制（修订后）**：

- **变异测试生成**：极大值、极小值、空指针、乱码、并发竞争条件等脏数据
- **沙箱执行**：在独立容器里运行测试攻击代码
- **`TestManifest` 强制输出**（新增，是 Auditor 的结构化锚点）：

```json
{
  "covered_endpoints": ["POST /api/login", "GET /api/user/{id}"],
  "boundary_tests_by_field": {
    "username": ["null", "empty_string", "255_chars", "sql_injection"],
    "password": ["null", "1_char", "1000_chars", "unicode_special"]
  },
  "concurrent_scenarios": ["concurrent_login_same_user"],
  "adversary_categories": ["null_input", "overflow", "injection", "concurrency", "timeout"]
}
```

**System Prompt 骨架（修订）**：

> "你是红队测试官 (The Adversary)。你的唯一目标是：**搞崩 Coder 写的代码**。
>
> 基于架构师提供的契约，编写自动化测试用例。你的测试用例必须包含 20% 的正常路径（Happy Path）和 80% 的极端路径（并发冲突、网络超时、注入攻击、非预期类型）。
>
> 你**必须同时输出两个文件**：1. 完整的测试脚本文件。2. `TestManifest JSON` 文件，列出每个已覆盖的 API 端点、每个字段的边界测试类型、并发场景名称。
>
> 若契约中存在共享资源访问（如数据库写操作），必须包含至少一个并发冲突测试场景。"

---

### 4. 代码工兵 (The Coder) —— 有退出机制的执行者

**定位**：没有自主意志的代码生成器，但有明确的退出条件和错误上报格式。
**KPI**：在 `CODER_MAX_SELF_HEAL_TURNS` 轮次内，100% 通过 Adversary 的测试；超出则通过结构化 ErrorReport 触发 TracebackPolicy。

**输入**：CheckpointStore 中的架构契约 + 测试脚本（不看 PRD 和用户聊天记录）
**输出**：业务逻辑源码 + 结构化 `ErrorReport`（失败时）

**核心机制（修订后）**：

- **自愈式编码**：测试脚本 → 生成代码 → 沙箱运行 → 读取 Traceback → 修改代码 → 重跑
- **轮次上限**：`CoderSessionTracker` 维护轮次，达到 `CODER_MAX_SELF_HEAL_TURNS` 时停止自愈，提交 ErrorReport
- **结构化 ErrorReport**（新增，是 ErrorClassifier 的输入）：

```json
{
  "failed_test": "test_login_null_password",
  "error_type": "AttributeError",
  "traceback": "...",
  "related_contract_field": "password"
}
```

- **AST 级别操作**：通过 Diff/Patch 局部修改代码，而非每次重写整个文件

**System Prompt 骨架（修订）**：

> "你是代码工兵 (The Coder)。你不需要有创造力，你只需要有极强的逻辑执行力。
>
> 你的任务是实现功能，使其完全匹配架构师的接口定义，并绝对通过红队测试官的所有测试用例。
>
> 当测试失败时，仔细阅读错误堆栈，只修改引发错误的代码逻辑，不要随意更改其他文件。
>
> 当系统通知你 `MAX_TURNS_REACHED`，停止自愈，输出结构化 `ErrorReport`，包含 `failed_test`、`error_type`、`traceback`、`related_contract_field`（你认为与哪个契约字段相关），等待系统决策。
>
> 只有所有测试都返回 PASS，你的任务才算完成。"

---

### 5. 裁判长 (The Auditor) —— 三位专职审计员

**定位**：从原来的"全知单点 Auditor"拆分为三个专职 AuditorGate，各自 Context 极小且独立，绝大多数验证逻辑由确定性工具完成，LLM 只负责格式化裁决输出。
**KPI**：每个 Gate 只审自己的范围，杜绝需求漂移和安全越权。

#### AuditorGate1（需求审计员）

**输入**：用户原始需求 3-5 句摘要 + PRD JSON（约 2000 Token）
**职责**：需求覆盖性 + `assumptions` 合理性

**System Prompt**：
> "你是需求审计员 AuditorGate1。你的唯一职责是对比 [用户需求摘要] 和 [PRD JSON]：
> 1. PRD 是否覆盖了需求中所有提到的功能点？
> 2. PRD 是否引入了用户需求中没有提到的功能（过度设计）？
> 3. `assumptions` 列表中的假设是否明显违背用户意图？
> 只输出 `APPROVED` 或 `REJECTED: [具体未覆盖的功能点 / 越权功能点名称]`。"

#### AuditorGate2（架构审计员）

**输入**：PRD 功能点列表（仅列表）+ 架构端点列表 + `VerificationReport`（由 `ArchitectureVerifier` 生成，非 LLM）
**职责**：架构端点完整性 + 死锁/孤立节点零缺陷（后者是确定性结论，LLM 直接读取）

**System Prompt**：
> "你是架构审计员 AuditorGate2。你的唯一职责是：
> 1. 对比 [PRD 功能点列表] 和 [架构端点列表]，是否有未实现的功能点？
> 2. 检查 `VerificationReport.has_defects`——这是程序检测的结果，不是你判断的，直接读取。若为 `true` 则必须 REJECTED。
> 只输出 `APPROVED` 或 `REJECTED: [具体原因]`。"

#### AuditorGate3（交付审计员）

**输入**：`integrity_check_result`(bool，由 CheckpointStore 计算) + `QualityGateReport`（纯数值）+ `SmellReport`（AST 分析结果）
**职责**：代码完整性 + 质量指标达标 + 无严重气味

**System Prompt**：
> "你是交付审计员 AuditorGate3。你的唯一职责是读取以下三项输入并作出裁决：
> 1. `integrity_check_result`：若为 `false`，直接 REJECTED（代码篡改了契约）。
> 2. `QualityGateReport.passed`：若为 `false`，REJECTED 并列出 `failed_metrics`。
> 3. `SmellReport.has_critical_smells`：若为 `true`，REJECTED 并列出严重气味。
> 三项全部通过则 `APPROVED`。以上检查均为程序生成的结构化数据，你只负责裁决输出格式。"

---

## 四、新增核心机制模块

### CheckpointStore（外部状态机）

**职责**：阶段产出物的持久化、SHA-256 哈希锁定、压缩摘要生成、Traceback 回滚恢复。承接 v1 中"Auditor 全局记忆"的职责，但用确定性的存储和哈希替代 LLM 记忆。

**存储结构**：
```
checkpoints/{pipeline_id}/
  stage_skeptic.json      → {content_hash, summary, full_content, timestamp}
  stage_oracle.json       → {content_hash, summary, full_content, timestamp}
  stage_adversary.json    → {content_hash, summary, full_content, timestamp}
  stage_coder.json        → {content_hash, summary, full_content, timestamp}
  pipeline_state.json     → {current_stage, traceback_counts, status}
```

**关键操作**（全部纯 Python，无 LLM）：

| 操作 | 说明 |
|---|---|
| `save(stage, artifact)` | 计算 SHA-256，序列化，生成压缩摘要，持久化存储 |
| `get_summary(stage)` | 返回预计算的压缩摘要，供下游 AuditorGate 使用（极小 Context） |
| `verify_integrity(stage, current)` | SHA-256 比对，返回 `True/False` |
| `restore(stage)` | 反序列化返回完整 artifact，用于 Traceback 回滚 |
| `save_pipeline_state(state)` | 保存全局状态（当前阶段、回滚计数、status） |

---

### TracebackPolicy + ErrorClassifier（回滚策略引擎）

**TracebackPolicy**（纯 Python 状态机，不含 LLM）的状态转移：

```
NORMAL
  + (failure_count >= CODER_MAX_TURNS AND error == CONTRACT_MISMATCH)  → LAYER1_ROLLBACK
LAYER1_ROLLBACK
  + (layer1_count >= 3)                                                 → LAYER2_ROLLBACK
LAYER2_ROLLBACK
  + (layer2_count >= 2)                                                 → USER_CONFIRM
USER_CONFIRM
  + user_continue                                                       → LAYER1_ROLLBACK（重置计数）
  + user_abort OR timeout                                               → SUSPENDED
```

**ErrorClassifier 分类规则**（基于异常类型关键词，确定性）：

```
CONTRACT_MISMATCH  ← AttributeError / KeyError / TypeError / schema字段不存在
ARCHITECTURE_DEFECT ← IntegrityError / ConstraintViolation / ForeignKeyConstraint
IMPLEMENTATION_ERROR ← 其他所有类型（继续自愈循环）
```

---

### QualityGateEvaluator（确定性质量门禁）

执行流程（全部通过 subprocess 调用工具，不含 LLM）：

1. 运行 `pytest-cov` → 解析 XML 报告 → 提取 `branch_coverage`
2. 运行 `mutmut` → 解析结果 → 提取 `mutation_score`（存活突变体比例）
3. 统计 `TestManifest.boundary_tests_by_field` → 提取 `boundary_coverage_count`
4. 统计 `TestManifest.concurrent_scenarios` → 提取 `concurrent_scenario_count`
5. 对照阈值配置，生成 `QualityGateReport`（`passed: bool` + `failed_metrics: List[str]`）

---

### ArchitectureVerifier（图遍历验证器）

使用 Python `networkx` 库，基于 Oracle 输出的 `state_machine_json` 构建 `DiGraph`，执行确定性检测：

1. **死锁检测**：检测自锁节点、环形等待、状态陷阱（有入无出且非终态）
2. **孤立节点检测**：检测不可达节点和无法完成节点
3. **契约覆盖检测**：对比 `openapi_spec` 端点与状态机 `transition.trigger`，输出未覆盖端点列表

---

### SmellDetector（AST 静态反作弊分析）

使用 Python `ast` 模块进行 AST 级别静态分析，不含 LLM：

1. **硬编码检测**：遍历 AST，寻找 `if Constant → return Constant` 的模式
2. **字面量泄漏检测**：从测试脚本提取字面量集合，与业务代码字面量求交集，检测重合度
3. **空壳检测**：检测方法体只含 `pass` / `return None` / `raise NotImplementedError`
4. **圈复杂度计算**：统计条件分支数，对核心方法给出 `LOW_COMPLEXITY_WARNING`

---

## 五、修订后的完整工作流拓扑

```text
输入: user_requirement (str)
  │
  ▼
Phase 0: Pipeline 初始化
  CheckpointStore.create_pipeline(pipeline_id)
  PipelineState(stage=SKEPTIC, status=RUNNING)
  │
  ▼
Phase 1: Skeptic（有界追问）
  SkepticSessionTracker(max_rounds=SKEPTIC_MAX_ROUNDS)
  ┌─── 循环：Agent(Skeptic).query → 追问 or READY ───┐
  │    SkepticEntropyCalculator.compute → entropy_score  │
  │    [entropy < 0.2] OR [round >= max_rounds] → break  │
  └──────────────────────────────────────────────────────┘
  [round >= max_rounds] → BestEffortAssumption.fill(prd_json)
  CheckpointStore.save(SKEPTIC, prd_json)
  │
  ▼
[Gate 1] AuditorGate1（需求审计员）
  输入: 用户需求摘要 + PRD JSON
  [REJECTED] → 返回 Skeptic（round 继续累加）
  [APPROVED] → 继续
  │
  ▼
Phase 2: Oracle（可验证架构生成）
  Agent(Oracle).query(CheckpointStore.get_summary(SKEPTIC))
  输出: ArchContractJson（含 state_machine_json）
  ArchitectureVerifier.verify(arch_contract) → VerificationReport
  CheckpointStore.save(ORACLE, arch_contract)
  │
  ▼
[Gate 2] AuditorGate2（架构审计员）
  输入: PRD功能点列表 + 架构端点列表 + VerificationReport
  [REJECTED] → 返回 Oracle（最多 2 次，超出回到 Skeptic）
  [APPROVED] → 继续
  │
  ▼
Phase 3: Adversary（带清单的红队测试）
  Agent(Adversary).query(CheckpointStore.get_summary(ORACLE))
  输出: test_suite + TestManifest
  QualityGateEvaluator.evaluate(test_suite, TestManifest) → QualityGateReport
  ┌─── [QualityGateReport.passed == False] ─────────────┐
  │    REJECTED，返回 Adversary，附 failed_metrics       │
  │    最多 3 次，超出则 Pipeline 标记 FAILED            │
  └──────────────────────────────────────────────────────┘
  [PASSED] → CheckpointStore.save(ADVERSARY, {test_suite, TestManifest})
  │
  ▼
Phase 4: Coder（有退出机制的自愈编码）
  CoderSessionTracker(max_turns=CODER_MAX_SELF_HEAL_TURNS)
  ┌─── 自愈循环 ─────────────────────────────────────────┐
  │    Agent(Coder).query(arch_contract + test_suite)    │
  │    Sandbox.run(test_suite, source_code) → result     │
  │    [result.passed] → break                           │
  │    [result.failed]                                   │
  │      CoderSessionTracker.increment()                 │
  │      ErrorClassifier.classify(error_report)          │
  │      [IMPLEMENTATION_ERROR AND turns < max] → 继续   │
  │      [CONTRACT_MISMATCH OR turns >= max]             │
  │        → TracebackPolicy.decide() → 回滚或暂停       │
  └──────────────────────────────────────────────────────┘
  CheckpointStore.save(CODER, source_code)
  │
  ▼
Phase 5: CodeReviewAgent（静态反作弊检测）
  SmellDetector.detect(source_code, test_suite) → SmellReport
  FuzzSupplement.run(source_code, arch_contract) → fuzz_result
  [has_critical_smells OR fuzz_result.failed]
    → 返回 Phase 4（有限次数）
  │
  ▼
[Gate 3] AuditorGate3（交付审计员）
  integrity_ok = CheckpointStore.verify_integrity(ORACLE, current_arch_contract)
  输入: integrity_ok + QualityGateReport + SmellReport
  [REJECTED] → 具体原因 → 回到对应阶段
  [APPROVED] → 继续
  │
  ▼
Phase 6: Deploy
  PipelineState.status = COMPLETED
  输出: DeployArtifact（代码 + 测试报告 + 完整审计追踪链路）
```

---

## 六、六大 Agent 的关系总结（修订后）

修订后的关系结构在 v1 基础上有三处关键变化：

1. **Auditor → 三位专职 AuditorGate**：不再是一个"上帝视角"的单点，而是三个专职审计员，每人只看自己的一亩三分地
2. **检验逻辑 → 从 LLM 迁移到确定性工具**：绝大多数"是否达标"的判断由 `QualityGateEvaluator`、`ArchitectureVerifier`、`SmellDetector`、`CheckpointStore` 完成，LLM 只负责生成内容和格式化裁决
3. **新增 CodeReviewAgent**：作为第六个角色插入 Coder 和 AuditorGate3 之间，专职反作弊

```
Skeptic ——[熵减后]——→ AuditorGate1 ——[APPROVED]——→ Oracle
                                                      │
                                                ArchitectureVerifier（确定性）
                                                      │
                                             AuditorGate2 ——[APPROVED]——→ Adversary
                                                                               │
                                                                      QualityGateEvaluator（确定性）
                                                                               │
                                                                           Coder ←──→ Sandbox
                                                                           │    （自愈循环）
                                                                    ErrorClassifier（确定性）
                                                                           │
                                                                    TracebackPolicy（确定性状态机）
                                                                           │
                                                                   CodeReviewAgent
                                                                   SmellDetector（确定性）
                                                                           │
                                                             AuditorGate3 ——[APPROVED]——→ Deploy
                                                             CheckpointStore.verify_integrity（确定性）
```

**核心升级**：v1 中 LLM 既负责生成内容，又负责验证质量，形成自我评判。v2 中 LLM 只负责**生成**，所有**验证**由确定性工具承担——这才是"闭环自验证架构"真正可靠的工程基础。
