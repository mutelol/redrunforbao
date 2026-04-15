from __future__ import annotations

import unittest

from curly_agent.assets import choose_cover_design
from curly_agent.models import CandidateItem


class CoverDesignTests(unittest.TestCase):
    def test_cover_design_is_stable_for_same_item(self) -> None:
        item = CandidateItem(
            source_section="new_arrivals",
            title="着ぐるみマスコットチャーム☆ハローキティいちごちゃん",
            url="https://curlycollection.jp/shop/products/detail/85741",
            image_url="https://curlycollection.jp/a.jpg",
            position=1,
        )
        first = choose_cover_design(item, "草莓挂件\n有点戳我", "新品速递 | 温柔可爱")
        second = choose_cover_design(item, "草莓挂件\n有点戳我", "新品速递 | 温柔可爱")
        self.assertEqual(first["template"], second["template"])
        self.assertEqual(first["name"], second["name"])


if __name__ == "__main__":
    unittest.main()
