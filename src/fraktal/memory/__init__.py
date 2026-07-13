"""Persistent memory store — SQLite and JSON backends.

Survives across sessions. The Orchestrator uses this to recall
past decisions and task outcomes.
"""

from __future__ import annotations

import json
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class MemoryEntry:
    id: int
    content: str
    category: str  # note, decision, task, project-fact
    tags: list[str]
    timestamp: float


class MemoryStore(ABC):
    @abstractmethod
    def remember(self, content: str, category: str = "note", tags: list[str] | None = None) -> int:
        ...

    @abstractmethod
    def recall(self, entry_id: int) -> MemoryEntry | None:
        ...

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        ...

    @abstractmethod
    def recent(self, limit: int = 10) -> list[MemoryEntry]:
        ...


class SQLiteMemory(MemoryStore):
    """SQLite-backed persistent memory."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS memories ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  content TEXT NOT NULL,"
            "  category TEXT DEFAULT 'note',"
            "  tags TEXT DEFAULT '[]',"
            "  timestamp REAL"
            ")"
        )
        self.conn.commit()

    def remember(self, content: str, category: str = "note", tags: list[str] | None = None) -> int:
        tags_json = json.dumps(tags or [])
        cur = self.conn.execute(
            "INSERT INTO memories (content, category, tags, timestamp) VALUES (?, ?, ?, ?)",
            (content, category, tags_json, time.time()),
        )
        self.conn.commit()
        return cur.lastrowid

    def recall(self, entry_id: int) -> MemoryEntry | None:
        cur = self.conn.execute("SELECT * FROM memories WHERE id = ?", (entry_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_entry(row)

    def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        cur = self.conn.execute(
            "SELECT * FROM memories WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query}%", limit),
        )
        return [self._row_to_entry(row) for row in cur.fetchall()]

    def recent(self, limit: int = 10) -> list[MemoryEntry]:
        cur = self.conn.execute(
            "SELECT * FROM memories ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_entry(row) for row in cur.fetchall()]

    def _row_to_entry(self, row) -> MemoryEntry:
        return MemoryEntry(
            id=row[0],
            content=row[1],
            category=row[2],
            tags=json.loads(row[3]) if isinstance(row[3], str) else row[3],
            timestamp=row[4],
        )


class JSONMemory(MemoryStore):
    """JSON-file-backed memory (simpler, no dependencies)."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]")
        self._entries: list[dict] = json.loads(self.path.read_text())
        self._next_id = max((e["id"] for e in self._entries), default=0) + 1

    def _save(self):
        self.path.write_text(json.dumps(self._entries, indent=2))

    def remember(self, content: str, category: str = "note", tags: list[str] | None = None) -> int:
        entry_id = self._next_id
        self._next_id += 1
        self._entries.append({
            "id": entry_id,
            "content": content,
            "category": category,
            "tags": tags or [],
            "timestamp": time.time(),
        })
        self._save()
        return entry_id

    def recall(self, entry_id: int) -> MemoryEntry | None:
        for e in self._entries:
            if e["id"] == entry_id:
                return MemoryEntry(**e)
        return None

    def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        q = query.lower()
        matches = [e for e in self._entries if q in e["content"].lower()]
        matches.sort(key=lambda e: e["timestamp"], reverse=True)
        return [MemoryEntry(**e) for e in matches[:limit]]

    def recent(self, limit: int = 10) -> list[MemoryEntry]:
        sorted_entries = sorted(self._entries, key=lambda e: e["timestamp"], reverse=True)
        return [MemoryEntry(**e) for e in sorted_entries[:limit]]


def create_memory(backend: str = "sqlite", path: Path | None = None) -> MemoryStore:
    """Factory for memory stores."""
    if path is None:
        path = Path.cwd() / ".fraktal" / "memory"
    path = Path(path)

    if backend == "sqlite":
        return SQLiteMemory(path if path.suffix == ".db" else path.with_suffix(".db"))
    elif backend == "json":
        return JSONMemory(path if path.suffix == ".json" else path.with_suffix(".json"))
    else:
        raise ValueError(f"Unknown memory backend: {backend}. Use 'sqlite' or 'json'.")
