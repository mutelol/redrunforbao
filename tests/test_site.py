from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from curly_agent.site import build_static_site


class StaticSiteTests(unittest.TestCase):
    def test_build_static_site_creates_self_contained_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runs_root = root / "runs"
            run_dir = runs_root / "20260415-sample"
            assets_dir = run_dir / "assets"
            assets_dir.mkdir(parents=True)

            (assets_dir / "primary.jpg").write_bytes(b"fake-jpg")
            (assets_dir / "cover.svg").write_text("<svg></svg>", encoding="utf-8")
            (run_dir / "content-pack.md").write_text(
                "# Curly 内容包\n\n## 1. 选题摘要\n\n- 测试标题\n\n## 6. Post Draft\n\n- Opening:\n  这是一段测试正文。",
                encoding="utf-8",
            )
            (run_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "generated_at": "2026-04-15T12:11:56",
                        "selected_item": {
                            "title": "测试原始标题",
                            "url": "https://curlycollection.jp/example",
                            "content_type": "新品速递",
                        },
                        "content_pack": {
                            "summary": "一段摘要",
                            "titles": ["一条更适合展示的标题"],
                            "tags": ["CurlyCollection", "可爱小物"],
                            "post_draft": {
                                "opening": "这是一段开头",
                                "body": "这是一段正文",
                                "closing": "这是一段结尾",
                            },
                            "image_plan": {
                                "cover_design": {
                                    "template": "sticker-frame",
                                    "palette": "sky-jelly",
                                }
                            },
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            site_root = root / "site"
            index_path = build_static_site(root, runs_root, site_root)

            self.assertTrue(index_path.exists())
            self.assertTrue((site_root / ".nojekyll").exists())
            self.assertTrue((site_root / "records" / "20260415-sample" / "assets" / "primary.jpg").exists())
            self.assertTrue((site_root / "items" / "20260415-sample.html").exists())

            data = json.loads((site_root / "data.json").read_text(encoding="utf-8"))
            self.assertEqual(data["generated_count"], 1)
            first = data["items"][0]
            self.assertEqual(first["cover_url"], "records/20260415-sample/assets/cover.svg")
            self.assertEqual(first["detail_url"], "./items/20260415-sample.html")
            self.assertNotIn("../runs", first["cover_url"])


if __name__ == "__main__":
    unittest.main()
