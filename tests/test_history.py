from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from curly_agent.history import HistoryStore
from curly_agent.models import CandidateItem


class HistoryStoreTests(unittest.TestCase):
    def test_import_existing_runs_marks_item_seen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "history.sqlite3"
            runs_root = root / "runs"
            run_dir = runs_root / "20260415-sample"
            run_dir.mkdir(parents=True)
            (run_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "generated_at": "2026-04-15T10:30:00",
                        "selected_item": {
                            "url": "https://curlycollection.jp/shop/products/detail/85741",
                            "item_id": "cha4759",
                            "title": "sample",
                            "source_section": "new_arrivals",
                            "content_type": "新品速递",
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            store = HistoryStore(db_path)
            store.initialize()
            imported = store.import_existing_runs(runs_root)
            self.assertEqual(imported, 1)

            state = store.seen_state()
            self.assertIn("https://curlycollection.jp/shop/products/detail/85741", state.urls)
            self.assertIn("cha4759", state.item_ids)

    def test_unseen_items_filters_seen_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "history.sqlite3"
            store = HistoryStore(db_path)
            store.initialize()
            seen_item = CandidateItem(
                source_section="new_arrivals",
                title="seen",
                url="https://curlycollection.jp/shop/products/detail/85741",
                image_url="https://curlycollection.jp/a.jpg",
                position=1,
                item_id="cha4759",
            )
            new_item = CandidateItem(
                source_section="new_arrivals",
                title="new",
                url="https://curlycollection.jp/shop/products/detail/85742",
                image_url="https://curlycollection.jp/b.jpg",
                position=2,
                item_id="cha4760",
            )
            store.record_generated(seen_item, generated_at="2026-04-15T10:30:00", run_dir=Path(tmp))
            unseen = store.unseen_items([seen_item, new_item])
            self.assertEqual([item.url for item in unseen], [new_item.url])


if __name__ == "__main__":
    unittest.main()
