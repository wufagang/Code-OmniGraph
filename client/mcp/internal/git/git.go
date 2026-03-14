package git

import (
	"fmt"
	"github.com/go-git/go-git/v5"
)

type GitManager struct {
	repoPath string
}

func NewGitManager(repoPath string) *GitManager {
	return &GitManager{repoPath: repoPath}
}

// GetModifiedFiles returns files changed since last commit
func (g *GitManager) GetModifiedFiles() ([]string, error) {
	repo, err := git.PlainOpen(g.repoPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open repo: %w", err)
	}

	worktree, err := repo.Worktree()
	if err != nil {
		return nil, fmt.Errorf("failed to get worktree: %w", err)
	}

	status, err := worktree.Status()
	if err != nil {
		return nil, fmt.Errorf("failed to get status: %w", err)
	}

	var modifiedFiles []string
	for path, fileStatus := range status {
		if fileStatus.Worktree == git.Modified || fileStatus.Worktree == git.Untracked || fileStatus.Worktree == git.Added {
			modifiedFiles = append(modifiedFiles, path)
		}
	}

	return modifiedFiles, nil
}
