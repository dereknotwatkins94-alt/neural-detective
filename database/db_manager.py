import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)

    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("CREATE TABLE IF NOT EXISTS saves (slot INTEGER PRIMARY KEY, version INTEGER NOT NULL, case_id TEXT NOT NULL, payload TEXT NOT NULL, updated_at TEXT NOT NULL)")
        connection.commit()
        return connection
