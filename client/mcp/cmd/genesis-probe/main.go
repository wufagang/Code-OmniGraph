package main

import (
	"fmt"
	"os"

	"genesis-probe/internal/mcp"
	"github.com/spf13/cobra"
)

func main() {
	var rootCmd = &cobra.Command{
		Use:   "genesis-probe",
		Short: "Genesis Probe is the local client for Project Genesis",
	}

	var runCmd = &cobra.Command{
		Use:   "run",
		Short: "Run the Genesis Probe",
		Run: func(cmd *cobra.Command, args []string) {
			useMcp, _ := cmd.Flags().GetBool("mcp")
			if useMcp {
				mcp.StartServer()
			} else {
				fmt.Println("Running in normal mode...")
			}
		},
	}

	runCmd.Flags().Bool("mcp", false, "Run as MCP server over stdio")
	rootCmd.AddCommand(runCmd)

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
