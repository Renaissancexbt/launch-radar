"""Local sqlite store: remembers what the radar has already seen.

Zero dependencies — stdlib ``sqlite3`` only. One file, two tables:

* ``posts``   — every post ever ingested, with its latest score
* ``seen``    — dedup keys (author + first link / contract) so the same
                launch reposted from three accounts shows up once

Typical use::

    store = Store("radar.db")
    fresh = store.ingest(candidates)     # returns only the never-seen ones
    store.history(limit=20)              # last scored posts, newest first
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import Candidate

_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id          TEXT PRIMARY KEY,
    url         TEXT,
    author      TEXT,
    text        TEXT,
    score       INTEGER,
    status      TEXT,
    chain       TEXT,
    category    TEXT,
    first_seen  TEXT,
    last_seen   TEXT,
    payload     TEXT
);
CREATE TABLE IF NOT EXISTS seen (
    key         TEXT PRIMARY KEY,
    post_id     TEXT,
    first_seen  TEXT
);
CREATE INDEX IF NOT EXISTS posts_score ON posts(score DESC);
CREATE INDEX IF NOT EXISTS posts_first_seen ON posts(first_seen DESC);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def dedup_key(c: Candidate) -> str:
    """Author + strongest piece of evidence. Two posts from the same handle
    pointing at the same contract or link are the same launch."""
    handle = c.post.author.handle.lower()
    if c.contracts:
        return f"{handle}|ca:{c.contracts[0].lower()}"
    if c.links:
        return f"{handle}|link:{c.links[0].lower().rstrip('/')}"
    return f"{handle}|post:{c.post.id}"


class Store:
    def __init__(self, path: str | Path = "radar.db") -> None:
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)

    # -- writes -------------------------------------------------------------

    def ingest(self, cands: Iterable[Candidate]) -> list[Candidate]:
        """Store every candidate; return the ones that are new by dedup key."""
        fresh: list[Candidate] = []
        now = _now()
        with self.conn:
            for c in cands:
                key = dedup_key(c)
                row = self.conn.execute("SELECT post_id FROM seen WHERE key = ?", (key,)).fetchone()
                is_new = row is None
                if is_new:
                    self.conn.execute(
                        "INSERT INTO seen(key, post_id, first_seen) VALUES (?, ?, ?)",
                        (key, c.post.id, now),
                    )
                    fresh.append(c)
                self.conn.execute(
                    """INSERT INTO posts(id, url, author, text, score, status, chain, category,
                                         first_seen, last_seen, payload)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                           score = excluded.score,
                           status = excluded.status,
                           last_seen = excluded.last_seen,
                           payload = excluded.payload""",
                    (c.post.id, c.post.url, c.post.author.handle, c.post.text, c.score, c.status,
                     c.chain, c.category, now, now, json.dumps(c.to_dict(), ensure_ascii=False)),
                )
        return fresh

    # -- reads --------------------------------------------------------------

    def history(self, limit: int = 50, minimum: int = 0) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM posts WHERE score >= ? ORDER BY first_seen DESC, score DESC LIMIT ?",
            (minimum, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def top(self, limit: int = 20) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM posts ORDER BY score DESC, first_seen DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0])

    def close(self) -> None:
        self.conn.close()


__all__ = ["Store", "dedup_key"]
