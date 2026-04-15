from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import CandidateItem


@dataclass
class SeenState:
    urls: set[str]
    item_ids: set[str]


class HistoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS generated_items (
                    item_url TEXT PRIMARY KEY,
                    item_id TEXT,
                    title TEXT NOT NULL,
                    source_section TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    first_generated_at TEXT NOT NULL,
                    last_generated_at TEXT NOT NULL,
                    last_run_dir TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_generated_items_item_id ON generated_items(item_id)"
            )
            conn.commit()
        finally:
            conn.close()

    def import_existing_runs(self, runs_root: Path) -> int:
        if not runs_root.exists():
            return 0
        imported = 0
        conn = sqlite3.connect(self.db_path)
        try:
            for metadata_path in sorted(runs_root.glob("*/metadata.json")):
                try:
                    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                item = payload.get("selected_item") or {}
                item_url = (item.get("url") or "").strip()
                title = (item.get("title") or "").strip()
                if not item_url or not title:
                    continue
                item_id = (item.get("item_id") or "").strip() or None
                generated_at = (payload.get("generated_at") or "").strip() or metadata_path.stat().st_mtime_ns
                content_type = (item.get("content_type") or "").strip() or "unknown"
                source_section = (item.get("source_section") or "").strip() or "unknown"
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO generated_items
                    (item_url, item_id, title, source_section, content_type, first_generated_at, last_generated_at, last_run_dir)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_url,
                        item_id,
                        title,
                        source_section,
                        content_type,
                        str(generated_at),
                        str(generated_at),
                        str(metadata_path.parent.resolve()),
                    ),
                )
                imported += cursor.rowcount
            conn.commit()
        finally:
            conn.close()
        return imported

    def seen_state(self) -> SeenState:
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("SELECT item_url, COALESCE(item_id, '') FROM generated_items").fetchall()
        finally:
            conn.close()
        urls = {row[0] for row in rows if row[0]}
        item_ids = {row[1] for row in rows if row[1]}
        return SeenState(urls=urls, item_ids=item_ids)

    def is_seen(self, item: CandidateItem, state: SeenState | None = None) -> bool:
        state = state or self.seen_state()
        return item.url in state.urls or (item.item_id and item.item_id in state.item_ids)

    def unseen_items(self, items: Iterable[CandidateItem], state: SeenState | None = None) -> list[CandidateItem]:
        state = state or self.seen_state()
        return [item for item in items if not self.is_seen(item, state)]

    def record_generated(self, item: CandidateItem, generated_at: str, run_dir: Path) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO generated_items
                (item_url, item_id, title, source_section, content_type, first_generated_at, last_generated_at, last_run_dir)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_url) DO UPDATE SET
                    item_id=excluded.item_id,
                    title=excluded.title,
                    source_section=excluded.source_section,
                    content_type=excluded.content_type,
                    last_generated_at=excluded.last_generated_at,
                    last_run_dir=excluded.last_run_dir
                """,
                (
                    item.url,
                    item.item_id or None,
                    item.title,
                    item.source_section,
                    item.content_type or "unknown",
                    generated_at,
                    generated_at,
                    str(run_dir.resolve()),
                ),
            )
            conn.commit()
        finally:
            conn.close()
