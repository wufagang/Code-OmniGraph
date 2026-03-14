<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/b3dc258a-6176-4165-8eac-b067b9792996

## Run Locally

**Prerequisites:**  Node.js


以下是已创建的核心文件及其功能：
1. go.mod: 定义了 Go 模块并引入了必要的依赖，如 mcp-go (MCP SDK)、go-sqlite3 (SQLite)、go-git (Git 集成) 和 cobra (CLI 框架)。
2. Makefile: 提供了简单的 build、clean 和 run 命令，方便编译和运行项目。
3. cmd/genesis-probe/main.go: 使用 Cobra 实现的 CLI 入口。支持 run --mcp 命令来启动 MCP Server。
4. internal/scanner/db.go: 封装了 SQLite 操作，自动创建 files 表，并提供 UpsertFile 和 GetFileHash 方法用于管理文件的增量状态。
5. internal/scanner/scanner.go: 实现了高性能的并发扫描引擎。它会根据 CPU 核心数启动多个 Worker，使用 filepath.WalkDir 遍历目录（自动跳过 .git、target 等目录），并发计算文件的 SHA-256 Hash，并与 SQLite 中的记录进行对比更新。
6. internal/git/git.go: 封装了 go-git 库，提供 GetModifiedFiles 方法，能够识别当前工作区中自上次 Commit 以来的变动文件（Modified, Untracked, Added）。
7. internal/mcp/server.go: 使用 mark3labs/mcp-go SDK 实现了一个基于 stdio 的 MCP Server。它注册了 TRD 中定义的 4 个核心工具：

   ls_project_tree
   fetch_context
   get_impact_analysis
   sync_delta



1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`
