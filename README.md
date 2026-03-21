<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/0c7b7f97-9237-42d6-abac-336a94a48488

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`


 方案亮点                                                                                                                                                                                                                       
                                                                                                                                                                                                                                   
  1. 核心洞察是对的：串通妥协（Collusion）问题                                                                                                                                                                                     
  把"信息不对称"和"物理隔离 Context"作为防止 AI 自我欺骗的手段，这是当前 Multi-Agent 领域真实存在的痛点，方案里对此有明确的解法。

  2. 单向阀门（Check-Valve）架构
  Auditor 作为每个阶段间的拦截节点，而不是最终一次性审计，这个设计很务实——错误越早被拦截，修复成本越低。

  3. 信息不对称（Visibility Masking）设计
  每个 Agent 只看它该看的东西，这是一个能有效减少 LLM 幻觉传播的工程手段，在实际系统中可落地。

  4. Adversary + Coder 的 GAN 模式
  把测试驱动和对抗生成结合，是整个方案最有创意的部分。