package scanner

import (
	"database/sql"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

type DB struct {
	conn *sql.DB
}

func NewDB(dbPath string) (*DB, error) {
	conn, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, err
	}

	db := &DB{conn: conn}
	if err := db.init(); err != nil {
		return nil, err
	}

	return db, nil
}

func (db *DB) init() error {
	query := `
	CREATE TABLE IF NOT EXISTS files (
		path TEXT PRIMARY KEY,
		hash TEXT,
		last_synced_at TIMESTAMP,
		status TEXT
	);`
	_, err := db.conn.Exec(query)
	return err
}

func (db *DB) UpsertFile(path, hash, status string) error {
	query := `
	INSERT INTO files (path, hash, last_synced_at, status)
	VALUES (?, ?, ?, ?)
	ON CONFLICT(path) DO UPDATE SET
		hash=excluded.hash,
		last_synced_at=excluded.last_synced_at,
		status=excluded.status;
	`
	_, err := db.conn.Exec(query, path, hash, time.Now(), status)
	return err
}

func (db *DB) GetFileHash(path string) (string, error) {
	var hash string
	err := db.conn.QueryRow("SELECT hash FROM files WHERE path = ?", path).Scan(&hash)
	if err != nil {
		if err == sql.ErrNoRows {
			return "", nil
		}
		return "", err
	}
	return hash, nil
}

func (db *DB) Close() error {
	return db.conn.Close()
}
