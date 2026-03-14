package scanner

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"sync"
)

type Scanner struct {
	db        *DB
	workspace string
}

func NewScanner(workspace string, db *DB) *Scanner {
	return &Scanner{
		db:        db,
		workspace: workspace,
	}
}

func (s *Scanner) Scan() error {
	filesChan := make(chan string, 100)
	var wg sync.WaitGroup

	// Start workers
	numWorkers := runtime.NumCPU()
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go s.worker(filesChan, &wg)
	}

	// Walk directory
	err := filepath.WalkDir(s.workspace, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			name := d.Name()
			if name == ".git" || name == "target" || name == ".idea" {
				return filepath.SkipDir
			}
			return nil
		}

		filesChan <- path
		return nil
	})

	close(filesChan)
	wg.Wait()

	return err
}

func (s *Scanner) worker(filesChan <-chan string, wg *sync.WaitGroup) {
	defer wg.Done()
	for path := range filesChan {
		hash, err := calculateHash(path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error hashing %s: %v\n", path, err)
			continue
		}

		// Check if hash changed
		oldHash, err := s.db.GetFileHash(path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error getting hash for %s: %v\n", path, err)
			continue
		}

		if oldHash != hash {
			err = s.db.UpsertFile(path, hash, "modified")
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error upserting %s: %v\n", path, err)
			}
		}
	}
}

func calculateHash(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()

	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", err
	}

	return hex.EncodeToString(h.Sum(nil)), nil
}
