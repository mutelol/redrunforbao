from __future__ import annotations

import unittest

from curly_agent.content import build_content_pack
from curly_agent.models import CandidateItem


class ContentPackTests(unittest.TestCase):
    def test_content_pack_has_expected_sections(self) -> None:
        item = CandidateItem(
            source_section="new_arrivals",
            title="オリジナルファブリック☆いちご x ピンク",
            url="https://curlycollection.jp/shop/products/detail/85797",
            image_url="https://curlycollection.jp/shop/upload/save_image/0413094842_69dc3d6a7c915.jpg",
            position=1,
            price_text="¥ 880",
            item_id="fab1238",
            is_new=True,
            detail_text="いちごを一面に散りばめたキュートな生地。コットン100%を使用しています。",
            detail_images=["https://curlycollection.jp/shop/upload/save_image/0413094842_69dc3d6a7c915.jpg"],
            content_type="新品速递",
            highlights=["材质写了 100% 棉，更适合走柔软、好搭配的分享口吻"],
        )
        pack = build_content_pack(item, "因为它是首页第一屏新品")
        self.assertEqual(len(pack["titles"]), 5)
        self.assertEqual(len(pack["hooks"]), 3)
        self.assertIn("main_cover_line", pack["cover"])
        self.assertIn("hero_image", pack["image_plan"])
        self.assertTrue(pack["comment_seeds"])


if __name__ == "__main__":
    unittest.main()
