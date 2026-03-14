package mcp

import (
	"context"
	"fmt"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func StartServer() {
	s := server.NewMCPServer(
		"Genesis Probe",
		"1.0.0",
		server.WithToolCapabilities(true),
	)

	// Tool: ls_project_tree
	lsProjectTreeTool := mcp.NewTool("ls_project_tree",
		mcp.WithDescription("返回项目的层级结构图"),
		mcp.WithString("path", mcp.Required(), mcp.Description("项目路径")),
	)
	s.AddTool(lsProjectTreeTool, handleLsProjectTree)

	// Tool: fetch_context
	fetchContextTool := mcp.NewTool("fetch_context",
		mcp.WithDescription("从后端获取调用拓扑及本地源码"),
		mcp.WithString("method_name", mcp.Required(), mcp.Description("方法名")),
		mcp.WithString("class_name", mcp.Required(), mcp.Description("类名")),
	)
	s.AddTool(fetchContextTool, handleFetchContext)

	// Tool: get_impact_analysis
	getImpactAnalysisTool := mcp.NewTool("get_impact_analysis",
		mcp.WithDescription("询问后端：修改此文件会影响哪些模块"),
		mcp.WithString("file_path", mcp.Required(), mcp.Description("文件路径")),
	)
	s.AddTool(getImpactAnalysisTool, handleGetImpactAnalysis)

	// Tool: sync_delta
	syncDeltaTool := mcp.NewTool("sync_delta",
		mcp.WithDescription("强制触发一次增量同步至后端"),
	)
	s.AddTool(syncDeltaTool, handleSyncDelta)

	// Start serving over stdio
	if err := server.ServeStdio(s); err != nil {
		fmt.Printf("Server error: %v\n", err)
	}
}

func handleLsProjectTree(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	path := request.Params.Arguments["path"].(string)
	return mcp.NewToolResultText(fmt.Sprintf("Project tree for %s", path)), nil
}

func handleFetchContext(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	methodName := request.Params.Arguments["method_name"].(string)
	className := request.Params.Arguments["class_name"].(string)
	return mcp.NewToolResultText(fmt.Sprintf("Context for %s.%s", className, methodName)), nil
}

func handleGetImpactAnalysis(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	filePath := request.Params.Arguments["file_path"].(string)
	return mcp.NewToolResultText(fmt.Sprintf("Impact analysis for %s", filePath)), nil
}

func handleSyncDelta(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	return mcp.NewToolResultText("Delta sync triggered successfully"), nil
}
